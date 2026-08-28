export const STEP_ORDER = [
  'website_scraper',
  'context_extractor',
  'competitor_finder',
  'news_fetcher',
  'curator',
  'briefing',
  'editor',
] as const

export type StepName = (typeof STEP_ORDER)[number]

export const STEP_LABELS: Record<StepName, string> = {
  website_scraper: 'Scraping website',
  context_extractor: 'Extracting company context',
  competitor_finder: 'Finding competitors',
  news_fetcher: 'Fetching news',
  curator: 'Curating results',
  briefing: 'Summarizing findings',
  editor: 'Assembling final brief',
}
