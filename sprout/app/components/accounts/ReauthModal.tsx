"use client";

import { useEffect, useState } from "react";
import { X, AlertTriangle, RefreshCw } from "lucide-react";
import { getReauthLinkToken } from "@/lib/api";
import { usePlaidLink } from "react-plaid-link";

interface ReauthModalProps {
  isOpen: boolean;
  plaidItemId: number;
  institutionName: string;
  token: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ReauthModal({
  isOpen,
  plaidItemId,
  institutionName,
  token,
  onClose,
  onSuccess,
}: ReauthModalProps) {
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch link token when modal opens
  useEffect(() => {
    if (isOpen && !linkToken) {
      fetchLinkToken();
    }
  }, [isOpen]);

  const fetchLinkToken = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const linkTokenString = await getReauthLinkToken(token, plaidItemId);
      setLinkToken(linkTokenString);
    } catch (err) {
      console.error("Failed to get reauth link token:", err);
      setError(
        err instanceof Error ? err.message : "Failed to initialize reauth"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: (public_token, metadata) => {
      console.log("Reauth successful:", metadata);
      onSuccess();
      onClose();
    },
    onExit: (err, metadata) => {
      if (err) {
        console.error("Plaid Link error:", err);
        setError(err.error_message || "Reauth failed");
      } else {
        console.log("User exited Plaid Link:", metadata);
      }
    },
  });

  const handleReconnect = () => {
    if (ready && linkToken) {
      open();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm bg-white/30"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-50 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Reconnect {institutionName}
              </h2>
              <p className="text-sm text-gray-500 mt-0.5">
                Authentication required
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {isLoading && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Initializing reconnection...</p>
            </div>
          )}

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-900">Error</p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {!isLoading && !error && linkToken && (
            <>
              <div className="mb-6">
                <p className="text-gray-700 mb-4">
                  Your connection to{" "}
                  <span className="font-semibold">{institutionName}</span> needs
                  to be refreshed to continue syncing your account data.
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-900">
                    <strong>What happens next:</strong>
                  </p>
                  <ul className="text-sm text-blue-800 mt-2 space-y-1 ml-4 list-disc">
                    <li>You'll be redirected to {institutionName}</li>
                    <li>Log in with your credentials</li>
                    <li>Your accounts will sync automatically</li>
                  </ul>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleReconnect}
                  disabled={!ready}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Reconnect Now
                </button>
              </div>
            </>
          )}

          {!isLoading && error && (
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Close
              </button>
              <button
                onClick={fetchLinkToken}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
