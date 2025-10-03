from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from app.models.request_models import RecommendationRequest
from app.models.response_models import (
    RecommendationResponse, 
    EnhancedRecommendationResponse,
    RecommendationInsights,
    TasteProfile
)
from app.services.gpt_service import GPTService
from app.services.hardcover_service import HardcoverService
from app.services.tmdb_service import TMDBService
from app.services.cache_service import CacheService, create_recommendation_cache_key, create_book_cache_key
from app.config import settings
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
gpt_service = GPTService()
hardcover_service = HardcoverService()
tmdb_service = TMDBService()
cache_service = CacheService(cache_dir=settings.cache_dir)

@router.get("/search-movies")
async def search_movies(query: str = Query(..., description="Movie search query")):
    """
    Search for movies using TMDB API
    """
    try:
        movies = await tmdb_service.search_movies(query)
        return {"results": movies}
    except Exception as e:
        logger.error(f"Error searching movies: {e}")
        # Return fallback movies on error
        movies = tmdb_service._get_fallback_movies()
        return {"results": movies}

@router.post("/recommend", response_model=EnhancedRecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest, 
    background_tasks: BackgroundTasks,
    include_insights: bool = Query(True, description="Include recommendation insights"),
    recommendation_type: str = Query("unified", description="Type of recommendation: 'unified' or 'individual'")
):
    """
    Get book recommendations based on movie preferences.
    
    - **unified**: Analyze overall taste profile and provide unified recommendations (default)
    - **individual**: Provide separate recommendations for each movie (legacy behavior)
    """
    start_time = time.time()
    
    try:
        # Validate input
        if not request.movies:
            raise HTTPException(status_code=400, detail="At least one movie is required")
        
        if len(request.movies) > settings.max_movies_per_request:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum {settings.max_movies_per_request} movies allowed per request"
            )
        
        # Create cache key (includes recommendation type)
        cache_key = create_recommendation_cache_key(
            request.movies, 
            request.preferences.model_dump() if request.preferences else None,
            recommendation_type
        )
        
        # Check cache first
        cached_result = await cache_service.get(cache_key, "recommendations")
        if cached_result:
            processing_time = time.time() - start_time
            if isinstance(cached_result, list):
                # Legacy format - wrap in new format
                cached_result = EnhancedRecommendationResponse(
                    recommendations=cached_result,
                    insights=await _generate_insights(request.movies, cached_result),
                    processing_time=processing_time,
                    cache_hit=True
                )
            return cached_result
        
        # Generate recommendations based on type
        if recommendation_type == "unified":
            recommendations = await _generate_unified_recommendations(request)
        else:
            recommendations = await _generate_individual_recommendations(request)
        
        # Enhance with book metadata from Hardcover
        enhanced_recommendations = await _enhance_with_metadata(recommendations)
        
        # Generate insights
        insights = await _generate_insights(request.movies, enhanced_recommendations) if include_insights else None
        
        # Create response
        response = EnhancedRecommendationResponse(
            recommendations=enhanced_recommendations,
            insights=insights,
            processing_time=time.time() - start_time,
            cache_hit=False
        )
        
        # Cache the result
        await cache_service.set(
            cache_key, 
            response, 
            expire=settings.cache_expire_seconds, 
            cache_type="recommendations"
        )
        
        # Schedule cache cleanup in background
        background_tasks.add_task(cleanup_old_cache)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        if settings.debug:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="An error occurred while generating recommendations")

async def _generate_unified_recommendations(request: RecommendationRequest) -> List[RecommendationResponse]:
    """Generate unified recommendations based on overall taste profile"""
    return await gpt_service.generate_recommendations(
        movies=request.movies,
        preferences=request.preferences
    )

async def _generate_individual_recommendations(request: RecommendationRequest) -> List[RecommendationResponse]:
    """Generate individual recommendations for each movie (legacy behavior)"""
    # This would use the old logic - generate recommendations for each movie separately
    # For now, we'll use the unified approach but split by movie
    all_recommendations = []
    
    for movie in request.movies:
        movie_recommendations = await gpt_service.generate_recommendations(
            movies=[movie],
            preferences=request.preferences
        )
        all_recommendations.extend(movie_recommendations)
    
    return all_recommendations

async def _enhance_with_metadata(recommendations: List[RecommendationResponse]) -> List[RecommendationResponse]:
    """Enhance recommendations with metadata from Hardcover"""
    enhanced_recommendations = []
    
    for rec in recommendations:
        enhanced_books = []
        
        # Process books concurrently for better performance
        book_tasks = []
        for book in rec.books:
            book_tasks.append(enhance_book_with_metadata(book))
        
        enhanced_books = await asyncio.gather(*book_tasks)
        rec.books = enhanced_books
        enhanced_recommendations.append(rec)
    
    return enhanced_recommendations

async def enhance_book_with_metadata(book):
    """Enhance a book recommendation with metadata from Hardcover"""
    try:
        # Create cache key for book metadata
        book_cache_key = create_book_cache_key(book.title, book.author)
        
        # Check cache first
        cached_metadata = await cache_service.get(book_cache_key, "books")
        
        if cached_metadata:
            # Apply cached metadata
            if cached_metadata.get('cover_url'):
                book.cover_url = cached_metadata['cover_url']
            if cached_metadata.get('rating'):
                book.rating = cached_metadata['rating']
            if cached_metadata.get('hardcover_url'):
                book.hardcover_url = cached_metadata['hardcover_url']
            if cached_metadata.get('genre_tags'):
                book.genre_tags = cached_metadata.get('genres', [])
            if cached_metadata.get('isbn'):
                book.isbn = cached_metadata['isbn']
            if cached_metadata.get('publication_year'):
                book.publication_year = cached_metadata['publication_year']
            if cached_metadata.get('page_count'):
                book.page_count = cached_metadata['page_count']
            if cached_metadata.get('publisher'):
                book.publisher = cached_metadata['publisher']
            if cached_metadata.get('hardcover_id'):
                book.hardcover_id = cached_metadata['hardcover_id']
            if cached_metadata.get('users_count'):
                book.users_count = cached_metadata['users_count']
            if cached_metadata.get('description'):
                book.description = cached_metadata['description']
        else:
            # Fetch from Hardcover API
            book_metadata = await hardcover_service.get_book_metadata(book.title, book.author)
            
            if book_metadata:
                # Apply metadata
                book.cover_url = book_metadata.get('cover_url')
                book.rating = book_metadata.get('rating')
                book.hardcover_url = book_metadata.get('url')
                book.genre_tags = book_metadata.get('genres', [])
                book.isbn = book_metadata.get('isbn')
                book.publication_year = book_metadata.get('publication_year')
                book.page_count = book_metadata.get('page_count')
                book.publisher = book_metadata.get('publisher')
                book.hardcover_id = book_metadata.get('hardcover_id')
                book.users_count = book_metadata.get('users_count')
                book.description = book_metadata.get('description')
                
                # Cache the metadata
                await cache_service.set(
                    book_cache_key, 
                    book_metadata, 
                    expire=settings.book_cache_expire_seconds, 
                    cache_type="books"
                )
            else:
                logger.warning(f"No metadata found for book: {book.title} by {book.author}")
        
        return book
        
    except Exception as e:
        # Log error but don't fail the request
        logger.error(f"Error enhancing book metadata for '{book.title}': {e}")
        return book

async def _generate_insights(movies: List[str], recommendations: List[RecommendationResponse]) -> RecommendationInsights:
    """Generate insights about the recommendations"""
    try:
        # Extract themes from taste profiles
        all_themes = []
        total_confidence = 0
        profile_count = 0
        
        for rec in recommendations:
            if rec.taste_profile:
                all_themes.extend(rec.taste_profile.themes)
                if rec.taste_profile.confidence_score:
                    total_confidence += rec.taste_profile.confidence_score
                    profile_count += 1
        
        # Calculate dominant themes
        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        dominant_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        dominant_themes = [theme for theme, count in dominant_themes]
        
        # Calculate genre diversity (simplified)
        all_genres = set()
        for rec in recommendations:
            for book in rec.books:
                if book.genre_tags:
                    all_genres.update(book.genre_tags)
        
        genre_diversity_score = min(1.0, len(all_genres) / 10)  # Normalize to 0-1
        
        # Calculate average confidence
        avg_confidence = total_confidence / profile_count if profile_count > 0 else 0.5
        
        return RecommendationInsights(
            total_movies_analyzed=len(movies),
            dominant_themes=dominant_themes,
            genre_diversity_score=genre_diversity_score,
            recommendation_confidence=avg_confidence,
            alternative_suggestions=[]  # Could add logic for alternative suggestions
        )
        
    except Exception as e:
        print(f"Error generating insights: {e}")
        return RecommendationInsights(
            total_movies_analyzed=len(movies),
            dominant_themes=[],
            genre_diversity_score=0.5,
            recommendation_confidence=0.5
        )

async def cleanup_old_cache():
    """Background task to clean up old cache entries"""
    try:
        await cache_service._cleanup_expired_cache()
    except Exception as e:
        print(f"Cache cleanup error: {e}")

@router.get("/taste-profile")
async def analyze_taste_profile(
    movies: List[str] = Query(..., description="List of movies to analyze"),
    preferences: Optional[str] = Query(None, description="JSON string of user preferences")
):
    """
    Analyze and return the user's taste profile based on movie preferences
    """
    try:
        if not movies:
            raise HTTPException(status_code=400, detail="At least one movie is required")
        
        # Parse preferences if provided
        user_preferences = None
        if preferences:
            import json
            user_preferences = json.loads(preferences)
        
        # Analyze taste profile
        taste_profile = await gpt_service.analyze_taste_profile(movies, user_preferences)
        
        return {
            "movies": movies,
            "taste_profile": taste_profile,
            "analysis_timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if settings.debug:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error analyzing taste profile")

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring"""
    try:
        stats = await cache_service.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")

@router.delete("/cache/clear")
async def clear_cache(cache_type: str = Query(None)):
    """Clear cache entries (useful for development)"""
    try:
        await cache_service.clear_all(cache_type)
        return {"message": f"Cache cleared successfully" + (f" for type: {cache_type}" if cache_type else "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.post("/regenerate", response_model=EnhancedRecommendationResponse)
async def regenerate_recommendations(
    request: RecommendationRequest,
    recommendation_type: str = Query("unified", description="Type of recommendation: 'unified' or 'individual'")
):
    """Generate new recommendations without using cache"""
    try:
        # Validate input
        if not request.movies:
            raise HTTPException(status_code=400, detail="At least one movie is required")
        
        if len(request.movies) > settings.max_movies_per_request:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum {settings.max_movies_per_request} movies allowed per request"
            )
        
        # Clear existing cache for this request
        cache_key = create_recommendation_cache_key(
            request.movies, 
            request.preferences.model_dump() if request.preferences else None,
            recommendation_type
        )
        await cache_service.delete(cache_key, "recommendations")
        
        # Generate fresh recommendations
        start_time = time.time()
        
        if recommendation_type == "unified":
            recommendations = await _generate_unified_recommendations(request)
        else:
            recommendations = await _generate_individual_recommendations(request)
        
        # Enhance with metadata
        enhanced_recommendations = await _enhance_with_metadata(recommendations)
        
        # Generate insights
        insights = await _generate_insights(request.movies, enhanced_recommendations)
        
        # Create response
        response = EnhancedRecommendationResponse(
            recommendations=enhanced_recommendations,
            insights=insights,
            processing_time=time.time() - start_time,
            cache_hit=False
        )
        
        # Cache the new result
        await cache_service.set(
            cache_key, 
            response, 
            expire=settings.cache_expire_seconds, 
            cache_type="recommendations"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        if settings.debug:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="An error occurred while regenerating recommendations")