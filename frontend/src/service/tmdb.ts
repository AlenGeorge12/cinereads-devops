import { Movie } from '@/types';
import { CineReadsAPI } from './api';

const TMDB_API_KEY = '473496e0286c39ee2c92ec60c58ac047';
const TMDB_READ_ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NzM0OTZlMDI4NmMzOWVlMmM5MmVjNjBjNThhYzA0NyIsIm5iZiI6MTc1Mjk0ODgxOS4wNjIsInN1YiI6IjY4N2JlMDUzMjQyOWQ3NDI5M2Q5ODc5YyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bmVIZn4oME4P1WYm2ClDycDT_ackwpxIPoAAvRIULN8';
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
  private api: CineReadsAPI;

  constructor() {
    this.apiKey = TMDB_API_KEY;
    this.readAccessToken = TMDB_READ_ACCESS_TOKEN;
    this.api = new CineReadsAPI();
  }

  async searchMovies(query: string): Promise<Movie[]> {
    if (!query || query.trim().length < 2) {
      return this.getFallbackMovies(query);
    }

    try {
      console.log('🎬 Searching movies for:', query);

      // Call backend API instead of TMDB directly
      const response = await fetch(`${this.api.baseURL}/search-movies?query=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('🔄 Search results:', data.results);

      return data.results || this.getFallbackMovies(query);

    } catch (error) {
      console.error('💥 Error searching movies:', error);
      console.log('🔄 Using fallback movies');
      return this.getFallbackMovies(query);
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
        vote_average: 8.5,
        overview: 'A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.',
        popularity: 140.0
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
        overview: 'The lives of guards on Death Row are affected by one of their charges: a black man accused of child murder and rape, yet who has a mysterious gift.',
        popularity: 110.0
      },
      {
        id: 680,
        title: 'Pulp Fiction',
        poster_path: '/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg',
        release_date: '1994-09-10',
        vote_average: 8.5,
        overview: 'A burger-loving hit man, his philosophical partner, a drug-addled gangster\'s moll and a washed-up boxer converge in this sprawling, comedic crime caper.',
        popularity: 105.0
      },
      {
        id: 155,
        title: 'The Dark Knight',
        poster_path: '/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
        release_date: '2008-07-18',
        vote_average: 9.0,
        overview: 'Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations that plague the streets.',
        popularity: 100.0
      }
    ];

    // Filter movies based on query if provided
    if (queryLower) {
      const filtered = popularMovies.filter(movie =>
        movie.title.toLowerCase().includes(queryLower)
      );
      if (filtered.length > 0) {
        return filtered.slice(0, 6);
      }
    }

    // Return top movies if no specific match
    return popularMovies.slice(0, 6);
  }
}

export const tmdbService = new TMDBService();
