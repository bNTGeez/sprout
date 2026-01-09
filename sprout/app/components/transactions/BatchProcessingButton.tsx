"use client";

import { useState, useEffect, useRef } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { fetchUncategorizedCount, processBatchUncategorized } from "@/lib/api";

interface BatchProcessingButtonProps {
  token: string;
  onProcessingComplete?: () => void;
  onError?: (message: string) => void;
}

export function BatchProcessingButton({
  token,
  onProcessingComplete,
  onError,
}: BatchProcessingButtonProps) {
  const [count, setCount] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const countIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const processingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch uncategorized count
  const fetchCount = async () => {
    try {
      const uncategorizedCount = await fetchUncategorizedCount(token);
      setCount(uncategorizedCount);
      setIsLoading(false);
    } catch (error) {
      console.error("Failed to fetch uncategorized count:", error);
      setIsLoading(false);
    }
  };

  // Initial fetch and setup polling
  useEffect(() => {
    if (!token) return;

    // Fetch immediately
    fetchCount();

    // Poll every 30 seconds (only when not processing)
    countIntervalRef.current = setInterval(() => {
      fetchCount();
    }, 30000);

    return () => {
      if (countIntervalRef.current) {
        clearInterval(countIntervalRef.current);
      }
    };
  }, [token]); // Remove isProcessing from deps

  // Poll more frequently while processing
  useEffect(() => {
    if (isProcessing) {
      // Poll every 2 seconds during processing
      processingIntervalRef.current = setInterval(() => {
        fetchCount();
      }, 2000);
      
      // Clear the 30s interval while processing
      if (countIntervalRef.current) {
        clearInterval(countIntervalRef.current);
      }
    } else {
      // Stop fast polling
      if (processingIntervalRef.current) {
        clearInterval(processingIntervalRef.current);
        processingIntervalRef.current = null;
      }
      
      // Restart 30s polling if not already running
      if (!countIntervalRef.current && token) {
        countIntervalRef.current = setInterval(() => {
          fetchCount();
        }, 30000);
      }
    }

    return () => {
      if (processingIntervalRef.current) {
        clearInterval(processingIntervalRef.current);
      }
    };
  }, [isProcessing, token]);

  // Stop processing when count reaches 0
  useEffect(() => {
    if (isProcessing && count === 0) {
      setIsProcessing(false);
      if (onProcessingComplete) {
        onProcessingComplete();
      }
    }
  }, [count, isProcessing, onProcessingComplete]);

  const handleClick = async () => {
    if (count === 0 || isProcessing) return;

    setIsProcessing(true);
    try {
      await processBatchUncategorized(token);
      // Immediately fetch count to show progress
      await fetchCount();
    } catch (error) {
      console.error("Failed to start batch processing:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to start batch processing";
      if (onError) {
        onError(errorMessage);
      }
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <button
        type="button"
        disabled
        className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg opacity-50 cursor-not-allowed flex items-center gap-2"
      >
        <Loader2 className="w-4 h-4 animate-spin" />
        Loading...
      </button>
    );
  }

  const isDisabled = count === 0 || isProcessing;

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isDisabled}
      className={`relative px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 transition-all ${
        isDisabled
          ? "bg-gray-300 text-gray-500 cursor-not-allowed"
          : "bg-purple-600 text-white hover:bg-purple-700"
      }`}
      title={
        count === 0
          ? "All transactions categorized"
          : isProcessing
          ? "Processing in progress..."
          : `Categorize ${count} transactions`
      }
    >
      {isProcessing ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Sparkles className="w-4 h-4" />
      )}
      <span>
        {isProcessing ? "Processing..." : "Auto-Categorize"}
      </span>
      {count > 0 && (
        <span className="absolute -top-2 -right-2 h-6 min-w-6 px-1.5 bg-orange-500 text-white text-xs font-bold rounded-full flex items-center justify-center shadow-lg">
          {count}
        </span>
      )}
    </button>
  );
}
