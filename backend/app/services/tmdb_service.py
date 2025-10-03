import httpx
import asyncio
from typing import Optional, Dict, Any, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class TMDBService:
    def __init__(self):
        self.api_key = "473496e0286c39ee2c92ec60c58ac047"  # Same key as frontend
        self.read_access_token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NzM0OTZlMDI4NmMzOWVlMmM5MmVjNjBjNThhYzA0NyIsIm5iZiI6MTc1Mjk0ODgxOS4wNjIsInN1YiI6IjY4N2JlMDUzMjQyOWQ3NDI5M2Q5ODc5YyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bmVIZn4oME4P1WYm2ClDycDT_ackwpxIPoAAvRIULN8"
        self.base_url = "https://api.themoviedb.org/3"
        self.timeout = 10.0

    async def search_movies(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for movies using TMDB API
        """
        if not query or len(query.strip()) < 2:
            return self._get_fallback_movies()

        try:
            url = f"{self.base_url}/search/movie"
            params = {
                "query": query.strip(),
                "language": "en-US",
                "page": 1,
                "include_adult": False,
                "sort_by": "popularity.desc"
            }

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.read_access_token}"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    # Transform to match frontend expectations
                    movies = []
                    for movie in results[:10]:  # Limit to 10 results
                        movies.append({
                            "id": movie.get("id"),
                            "title": movie.get("title", ""),
                            "poster_path": movie.get("poster_path"),
                            "release_date": movie.get("release_date", ""),
                            "vote_average": movie.get("vote_average", 0),
                            "overview": movie.get("overview", ""),
                            "popularity": movie.get("popularity", 0)
                        })

                    if movies:
                        return movies

        except Exception as e:
            logger.error(f"Error searching TMDB: {e}")

        # Return fallback movies if API fails
        return self._get_fallback_movies()

    def _get_fallback_movies(self) -> List[Dict[str, Any]]:
        """
        Return hardcoded fallback movies when TMDB is unavailable
        """
        return [
            {
                "id": 550,
                "title": "Fight Club",
                "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
                "release_date": "1999-10-15",
                "vote_average": 8.4,
                "overview": "A ticking-time-bomb insomniac and a slippery soap salesman channel primal male aggression into a shocking new form of therapy.",
                "popularity": 100.0
            },
            {
                "id": 13,
                "title": "Forrest Gump",
                "poster_path": "/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg",
                "release_date": "1994-07-06",
                "vote_average": 8.5,
                "overview": "A man with a low IQ has accomplished great things in his life and been present during significant historic events.",
                "popularity": 95.0
            },
            {
                "id": 278,
                "title": "The Shawshank Redemption",
                "poster_path": "/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg",
                "release_date": "1994-09-23",
                "vote_average": 9.3,
                "overview": "Framed in the 1940s for the double murder of his wife and her lover, upstanding banker Andy Dufresne begins a new life at the Shawshank prison.",
                "popularity": 90.0
            },
            {
                "id": 238,
                "title": "The Godfather",
                "poster_path": "/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
                "release_date": "1972-03-14",
                "vote_average": 9.2,
                "overview": "Spanning the years 1945 to 1955, a chronicle of the fictional Italian-American Corleone crime family.",
                "popularity": 85.0
            },
            {
                "id": 680,
                "title": "Pulp Fiction",
                "poster_path": "/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
                "release_date": "1994-09-10",
                "vote_average": 8.5,
                "overview": "A burger-loving hit man, his philosophical partner, a drug-addled gangster's moll and a washed-up boxer converge in this sprawling, comedic crime caper.",
                "popularity": 80.0
            },
            {
                "id": 155,
                "title": "The Dark Knight",
                "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
                "release_date": "2008-07-18",
                "vote_average": 9.0,
                "overview": "Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations that plague the streets.",
                "popularity": 75.0
            }
        ]