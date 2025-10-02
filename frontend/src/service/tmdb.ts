import { Movie } from '@/types';

const TMDB_API_KEY = 'c68167085a4634779864f0d9a247fdec';
const TMDB_READ_ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjNjgxNjcwODVhNDYzNDc3OTg2NGYwZDlhMjQ3ZmRlYyIsIm5iZiI6MTc1OTQwNjE2OC42MTYsInN1YiI6IjY4ZGU2ODU4OWNmNDJlZWI3ZWZkMjIxNCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.z0zZReUb5kVc2qJHspOC0sY9T6nA6Guc7lv8NLwDWjc';
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';

interface TMDBMovie {
  id: number;
  title: string;
  poster_path: string | null;
  release_date: string;
  vote_average: number;
  overview: string;
  popularity: number;
}

interface TMDBSearchResponse {
  results: TMDBMovie[];
  total_results: number;
  total_pages: number;
}

class TMDBService {
  private apiKey: string;
  private readAccessToken: string;

  constructor() {
    this.apiKey = TMDB_API_KEY;
    this.readAccessToken = TMDB_READ_ACCESS_TOKEN;
  }

  async searchMovies(query: string): Promise<Movie[]> {
    if (!query || query.trim().length < 2) {
      return [];
    }

    try {
      console.log('🎬 Searching TMDB for:', query);
      
      // Use the modern Bearer token approach for better authentication
      const url = `${TMDB_BASE_URL}/search/movie?query=${encodeURIComponent(query)}&language=en-US&page=1&include_adult=false&sort_by=popularity.desc`;
      console.log('🔗 TMDB URL:', url);

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.readAccessToken}`
        }
      });

      console.log('📡 TMDB Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ TMDB API error:', response.status, errorText);
        throw new Error(`TMDB API error: ${response.status} - ${errorText}`);
      }

      const data: TMDBSearchResponse = await response.json();
      console.log('✅ TMDB Response data received:', data.total_results, 'results');
      
      if (!data.results || data.results.length === 0) {
        console.warn('⚠️ No results in TMDB response');
        return [];
      }

      // Enhanced sorting and filtering
      const sortedResults = data.results
        .filter(movie => {
          // Filter out movies with no title or very low quality data
          return movie.title && 
                 movie.title.trim().length > 0 && 
                 movie.popularity > 0;
        })
        .sort((a, b) => {
          // Multi-factor sorting for best results
          
          // 1. Prioritize exact matches in title
          const queryLower = query.toLowerCase();
          const aExactMatch = a.title.toLowerCase().includes(queryLower);
          const bExactMatch = b.title.toLowerCase().includes(queryLower);
          
          if (aExactMatch && !bExactMatch) return -1;
          if (!aExactMatch && bExactMatch) return 1;
          
          // 2. Sort by popularity (higher is better)
          if (Math.abs(b.popularity - a.popularity) > 10) {
            return b.popularity - a.popularity;
          }
          
          // 3. Sort by vote average for similar popularity
          if (Math.abs(b.vote_average - a.vote_average) > 0.5) {
            return b.vote_average - a.vote_average;
          }
          
          // 4. Prefer more recent releases
          const aYear = a.release_date ? new Date(a.release_date).getFullYear() : 0;
          const bYear = b.release_date ? new Date(b.release_date).getFullYear() : 0;
          return bYear - aYear;
        })
        .slice(0, 12); // Get top 12 results

      console.log('🎯 Processed TMDB results:', sortedResults.length, 'movies');
      
      // Format movies with proper poster URLs
      return sortedResults.map(movie => this.formatMovieWithPoster(movie));
    } catch (error) {
      console.error('💥 Error searching movies:', error);
      
      // Enhanced fallback with more movies based on search query
      const fallbackMovies = this.getFallbackMovies(query);
      console.log('🔄 Using fallback movies:', fallbackMovies.length);
      return fallbackMovies;
    }
  }

  private getFallbackMovies(query: string): Movie[] {
    const queryLower = query.toLowerCase();
    
    // Comprehensive fallback movie database
    const popularMovies: TMDBMovie[] = [
      {
        id: 27205,
        title: 'Inception',
        poster_path: '/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
        release_date: '2010-07-15',
        vote_average: 8.4,
        overview: 'Dom Cobb is a skilled thief who steals corporate secrets through the use of dream-sharing technology.',
        popularity: 151.0
      },
      {
        id: 603,
        title: 'The Matrix',
        poster_path: '/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg',
        release_date: '1999-03-30',
        vote_average: 8.2,
        overview: 'Set in the 22nd century, The Matrix tells the story of a computer hacker who joins a group of underground insurgents.',
        popularity: 143.2
      },
      {
        id: 157336,
        title: 'Interstellar',
        poster_path: '/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg',
        release_date: '2014-11-07',
        vote_average: 8.4,
        overview: 'The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel.',
        popularity: 139.5
      },
      {
        id: 155,
        title: 'The Dark Knight',
        poster_path: '/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
        release_date: '2008-07-18',
        vote_average: 8.5,
        overview: 'Batman raises the stakes in his war on crime with the help of Lt. Jim Gordon and District Attorney Harvey Dent.',
        popularity: 135.8
      },
      {
        id: 680,
        title: 'Pulp Fiction',
        poster_path: '/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg',
        release_date: '1994-09-10',
        vote_average: 8.3,
        overview: 'A burger-loving hit man, his philosophical partner, and a drug-addled gangster\'s moll navigate a world of criminals.',
        popularity: 128.4
      },
      {
        id: 13,
        title: 'Forrest Gump',
        poster_path: '/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg',
        release_date: '1994-06-23',
        vote_average: 8.2,
        overview: 'A man with a low IQ has accomplished great things in his life and been present during significant historic events.',
        popularity: 125.1
      },
      {
        id: 550,
        title: 'Fight Club',
        poster_path: '/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg',
        release_date: '1999-10-15',
        vote_average: 8.4,
        overview: 'An insomniac office worker and a devil-may-care soapmaker form an underground fight club.',
        popularity: 122.7
      },
      {
        id: 497,
        title: 'The Green Mile',
        poster_path: '/velWPhVMQeQKcxggNEU8YmIo52R.jpg',
        release_date: '1999-12-10',
        vote_average: 8.5,
        overview: 'The story of John Coffey, a giant black man convicted of the brutal murder of two little girls.',
        popularity: 119.3
      }
    ];
    
    // Filter movies based on search query
    const matchingMovies = popularMovies.filter(movie => 
      movie.title.toLowerCase().includes(queryLower) ||
      movie.overview.toLowerCase().includes(queryLower)
    );
    
    // Return matching movies, or top popular ones if no matches
    const resultMovies = matchingMovies.length > 0 ? matchingMovies : popularMovies.slice(0, 6);
    return resultMovies.map(movie => this.formatMovieWithPoster(movie));
  }

  async getMovieDetails(movieId: number): Promise<TMDBMovie | null> {
    try {
      const response = await fetch(
        `${TMDB_BASE_URL}/movie/${movieId}?language=en-US`,
        {
          headers: {
            'Accept': 'application/json',
            'Authorization': `Bearer ${this.readAccessToken}`
          }
        }
      );

      if (!response.ok) {
        throw new Error(`TMDB API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching movie details:', error);
      return null;
    }
  }

  formatMovieForDisplay(movie: TMDBMovie): string {
    const year = movie.release_date ? ` (${new Date(movie.release_date).getFullYear()})` : '';
    return `${movie.title}${year}`;
  }

  formatMovieWithPoster(movie: TMDBMovie): Movie {
    return {
      id: movie.id,
      title: movie.title,
      poster_path: movie.poster_path,
      poster_url: movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : null,
      release_date: movie.release_date,
      overview: movie.overview,
      vote_average: movie.vote_average,
      popularity: movie.popularity
    };
  }
}

export const tmdbService = new TMDBService();
export type { TMDBMovie };
