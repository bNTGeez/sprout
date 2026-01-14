"use client";

import { useState, useEffect, useMemo } from "react";
import { X } from "lucide-react";
import {
  PlaidLinkOptions,
  usePlaidLink,
  PlaidLinkOnExitMetadata,
  PlaidLinkOnSuccessMetadata,
} from "react-plaid-link";
import { createClient } from "@/lib/supabase/client";
import { getPlaidLinkToken, exchangePlaidToken } from "@/lib/api";

interface AddAccountsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  institutionName?: string; // Optional, not used in the UI anymore
}

export default function AddAccountsModal({
  isOpen,
  onClose,
  onSuccess,
  institutionName,
}: AddAccountsModalProps) {
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && !linkToken) {
      fetchLinkToken();
    }
  }, [isOpen]);

  const fetchLinkToken = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;
      if (!token) {
        throw new Error("Not authenticated");
      }
      setAuthToken(token);
      const newLinkToken = await getPlaidLinkToken(token);
      setLinkToken(newLinkToken);
    } catch (err) {
      console.error("Failed to get link token:", err);
      setError(err instanceof Error ? err.message : "Failed to initialize");
    } finally {
      setIsLoading(false);
    }
  };

  const config: PlaidLinkOptions = useMemo(() => {
    if (!linkToken || !authToken) {
      return {
        token: "",
        onSuccess: () => {},
        onExit: () => {},
        onEvent: () => {},
      };
    }

    return {
      onSuccess: async (
        public_token: string,
        metadata: PlaidLinkOnSuccessMetadata
      ) => {
        setIsLoading(true);
        setError(null);

        const institution_id = metadata?.institution?.institution_id;
        const institution_name = metadata?.institution?.name;

        try {
          await exchangePlaidToken(
            public_token,
            authToken!,
            institution_id || null,
            institution_name || null
          );
          onSuccess();
          onClose();
        } catch (err) {
          console.error("Failed to exchange token:", err);
          setError(err instanceof Error ? err.message : "Failed to add accounts");
        } finally {
          setIsLoading(false);
        }
      },
      onExit: (err, metadata: PlaidLinkOnExitMetadata) => {
        setIsLoading(false);
        if (err) {
          setError("Connection cancelled or failed");
        }
      },
      token: linkToken,
    };
  }, [linkToken, authToken, onSuccess, onClose]);

  const { open, ready } = usePlaidLink(config);

  useEffect(() => {
    if (isOpen && ready && linkToken && !isLoading) {
      open();
    }
  }, [isOpen, ready, linkToken, isLoading, open]);

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 backdrop-blur-sm bg-black/20 z-40 transition-all"
        onClick={onClose}
      />
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <div
          className="bg-white rounded-lg shadow-xl w-full max-w-md"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">
              Add More Accounts
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <div className="p-6">
            {isLoading && !error && (
              <div className="text-center py-8">
                <div className="inline-block h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
                <p className="text-gray-600">Opening Plaid Link...</p>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}

            {!isLoading && !error && (
              <div className="text-center py-4">
                <p className="text-gray-600 mb-4">
                  Connect additional accounts from any bank to add to your account list. You can add more accounts from the same institution or connect a different bank.
                </p>
                <button
                  onClick={() => {
                    if (ready && linkToken) {
                      setError(null);
                      open();
                    }
                  }}
                  disabled={!ready || !linkToken}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  Open Plaid Link
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
