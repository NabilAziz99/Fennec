/**
 * Hypothesis Filters
 *
 * Tabs, search, and sort controls for filtering hypothesis list
 */

import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Search, ArrowUpDown } from 'lucide-react';

export type FilterView = 'all' | 'active' | 'completed' | 'blocked' | 'vulnerable';
export type SortOption = 'priority' | 'status' | 'recent' | 'severity';

interface HypothesisFiltersProps {
  activeView: FilterView;
  onViewChange: (view: FilterView) => void;
  sortBy: SortOption;
  onSortChange: (sort: SortOption) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  counts: {
    all: number;
    active: number;
    completed: number;
    blocked: number;
    vulnerable: number;
  };
}

export function HypothesisFilters({
  activeView,
  onViewChange,
  sortBy,
  onSortChange,
  searchQuery,
  onSearchChange,
  counts,
}: HypothesisFiltersProps) {
  return (
    <div className="space-y-3">
      {/* View Tabs */}
      <Tabs value={activeView} onValueChange={(value) => onViewChange(value as FilterView)}>
        <TabsList className="grid w-full grid-cols-5 h-auto">
          <TabsTrigger value="all" className="flex flex-col sm:flex-row items-center gap-1 py-2">
            <span className="text-xs sm:text-sm">All</span>
            {counts.all > 0 && (
              <Badge
                variant="outline"
                className="ml-0 sm:ml-1 scale-75 sm:scale-100 bg-fennec-light-700 text-fennec-light-300 border-fennec-light-600"
              >
                {counts.all}
              </Badge>
            )}
          </TabsTrigger>

          <TabsTrigger value="active" className="flex flex-col sm:flex-row items-center gap-1 py-2">
            <span className="text-xs sm:text-sm">Active</span>
            {counts.active > 0 && (
              <Badge
                variant="outline"
                className="ml-0 sm:ml-1 scale-75 sm:scale-100 bg-blue-500/20 text-blue-400 border-blue-500/30"
              >
                {counts.active}
              </Badge>
            )}
          </TabsTrigger>

          <TabsTrigger value="completed" className="flex flex-col sm:flex-row items-center gap-1 py-2">
            <span className="text-xs sm:text-sm">Done</span>
            {counts.completed > 0 && (
              <Badge
                variant="outline"
                className="ml-0 sm:ml-1 scale-75 sm:scale-100 bg-green-500/20 text-green-400 border-green-500/30"
              >
                {counts.completed}
              </Badge>
            )}
          </TabsTrigger>

          <TabsTrigger value="blocked" className="flex flex-col sm:flex-row items-center gap-1 py-2">
            <span className="text-xs sm:text-sm">Blocked</span>
            {counts.blocked > 0 && (
              <Badge
                variant="outline"
                className="ml-0 sm:ml-1 scale-75 sm:scale-100 bg-orange-500/20 text-orange-400 border-orange-500/30"
              >
                {counts.blocked}
              </Badge>
            )}
          </TabsTrigger>

          <TabsTrigger value="vulnerable" className="flex flex-col sm:flex-row items-center gap-1 py-2">
            <span className="text-xs sm:text-sm">Vulns</span>
            {counts.vulnerable > 0 && (
              <Badge
                variant="outline"
                className="ml-0 sm:ml-1 scale-75 sm:scale-100 bg-red-500/20 text-red-400 border-red-500/30"
              >
                {counts.vulnerable}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Search and Sort */}
      <div className="flex flex-col sm:flex-row gap-2">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-fennec-light-900" />
          <Input
            type="text"
            placeholder="Search hypotheses..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9 bg-fennec-light-800 border-fennec-light-700 text-white placeholder:text-fennec-light-500"
          />
        </div>

        {/* Sort */}
        <Select value={sortBy} onValueChange={(value) => onSortChange(value as SortOption)}>
          <SelectTrigger className="w-full sm:w-[180px] bg-fennec-light-800 border-fennec-light-700 text-white">
            <ArrowUpDown className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent className="bg-fennec-light-800 border-fennec-light-700">
            <SelectItem value="priority" className="text-white hover:bg-fennec-light-700">
              Priority (High→Low)
            </SelectItem>
            <SelectItem value="status" className="text-white hover:bg-fennec-light-700">
              Status
            </SelectItem>
            <SelectItem value="recent" className="text-white hover:bg-fennec-light-700">
              Most Recent
            </SelectItem>
            <SelectItem value="severity" className="text-white hover:bg-fennec-light-700">
              Severity
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}

export default HypothesisFilters;
