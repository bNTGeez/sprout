import {
  exchangePlaidToken,
  getPlaidLinkToken,
  getPlaidItems,
} from "@/lib/api";
import { useState, useEffect, useMemo } from "react";
import {
  PlaidLinkOptions,
  usePlaidLink,
  PlaidLinkOnExitMetadata,
  PlaidLinkOnSuccessMetadata,
} from "react-plaid-link";
import { createClient } from "@/lib/supabase/client";

export default function ConnectBank() {
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const fetchLinkToken = async () => {
      try {
        // Get Supabase session token
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();

        const token = session?.access_token;
        if (!token) {
          setError("You must be logged in to connect a bank account.");
          setLoading(false);
          return;
        }

        setAuthToken(token);

        // Check if a Plaid item already exists for this user
        try {
          const items = await getPlaidItems(token);
          const hasItems = items?.plaid_items?.length > 0;
          setIsConnected(hasItems);
          if (hasItems) {
            setLoading(false);
            return;
          }
        } catch (itemsErr) {
          // Non-fatal: continue to attempt link token fetch
          console.warn("Unable to load Plaid items:", itemsErr);
        }

        const newLinkToken = await getPlaidLinkToken(token);
        setLinkToken(newLinkToken);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching Plaid link token:", error);
        setError("Failed to fetch Plaid link token. Please try again.");
        setLoading(false);
      }
    };
    fetchLinkToken();
  }, []);

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
        setLoading(true);
        setError(null);

        const institution_id = metadata?.institution?.institution_id;
        const institution_name = metadata?.institution?.name;

        // Exchange token and sync data
        exchangePlaidToken(
          public_token,
          authToken,
          institution_id || null,
          institution_name || null
        )
          .then(() => {
            setSuccess(true);
            setIsConnected(true);
          })
          .catch((error: any) => {
            console.error("Failed to exchange Plaid token:", error);
            // Don't block redirect - user can retry sync later
          })
          .finally(() => {
            setLoading(false);
            // Redirect to dashboard after short delay
            setTimeout(() => {
              window.location.replace("/dashboard");
            }, 1000);
          });
      },
      onExit: (err, metadata: PlaidLinkOnExitMetadata) => {
        setLoading(false);
        if (err) {
          setError("Connection cancelled or failed. Please try again.");
        }
      },
      token: linkToken,
    };
  }, [linkToken, authToken]);

  const { open, exit, ready } = usePlaidLink(config);

  if (loading) {
    return (
      <button
        disabled
        className="bg-gray-400 text-white px-6 py-2 rounded-lg font-semibold cursor-not-allowed"
      >
        {success ? "Connecting..." : "Loading..."}
      </button>
    );
  }

  return (
    <div className="flex flex-col items-end gap-2">
      {error && (
        <div className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded border border-red-200">
          {error}
        </div>
      )}
      {success && (
        <div className="text-green-600 text-sm bg-green-50 px-3 py-2 rounded border border-green-200">
          Bank connected successfully! Redirecting...
        </div>
      )}
      <button
        onClick={() => {
          if (linkToken && ready) {
            setError(null);
            setSuccess(false);
            open();
          }
        }}
        disabled={!ready || !linkToken || loading || isConnected}
        className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isConnected ? "Bank Connected" : "Connect Bank Account"}
      </button>
    </div>
  );
}
