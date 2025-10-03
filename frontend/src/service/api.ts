import { UserPreferences, RecommendationResponse, CacheStats, EnhancedRecommendationResponse } from '@/types';

export class CineReadsAPI {
  public baseURL: string;

  constructor(baseURL: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') {
    this.baseURL = `${baseURL}/api`;
  }

  async getRecommendations(
    movies: string[], 
    preferences: UserPreferences | null = null
  ): Promise<RecommendationResponse[]> {
    const response = await fetch(`${this.baseURL}/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        movies,
        preferences
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `API Error: ${response.status} ${response.statusText}`
      );
    }

    const data: EnhancedRecommendationResponse = await response.json();
    return data.recommendations;
  }

  async regenerateRecommendations(
    movies: string[], 
    preferences: UserPreferences | null = null
  ): Promise<RecommendationResponse[]> {
    const response = await fetch(`${this.baseURL}/regenerate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        movies,
        preferences
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `API Error: ${response.status} ${response.statusText}`
      );
    }

    const data: EnhancedRecommendationResponse = await response.json();
    return data.recommendations;
  }

  async getCacheStats(): Promise<CacheStats> {
    const response = await fetch(`${this.baseURL}/cache/stats`);
    
    if (!response.ok) {
      throw new Error(`Failed to get cache stats: ${response.status}`);
    }

    return response.json();
  }

  async clearCache(cacheType?: string): Promise<{ message: string }> {
    const url = cacheType 
      ? `${this.baseURL}/cache/clear?cache_type=${cacheType}`
      : `${this.baseURL}/cache/clear`;

    const response = await fetch(url, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error(`Failed to clear cache: ${response.status}`);
    }

    return response.json();
  }

  async healthCheck(): Promise<{
    status: string;
    cache_dir_exists: boolean;
    openai_configured: boolean;
    hardcover_configured: boolean;
    debug_mode: boolean;
  }> {
    const response = await fetch(`${this.baseURL.replace('/api', '')}/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return response.json();
  }
}