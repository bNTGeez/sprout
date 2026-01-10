"use client";

import { useState } from "react";
import { CheckCircle, AlertTriangle, XCircle, RefreshCw } from "lucide-react";

interface AccountHealthIndicatorProps {
  status: string;
  errorMessage?: string | null;
  institutionName?: string;
  onReauth?: () => void;
}

export default function AccountHealthIndicator({
  status,
  errorMessage,
  institutionName,
  onReauth,
}: AccountHealthIndicatorProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const handleReauthClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onReauth && typeof onReauth === "function") {
      onReauth();
    }
  };

  const getStatusConfig = () => {
    switch (status) {
      case "good":
      case "active":
        return {
          icon: CheckCircle,
          label: "Active",
          color: "text-green-600",
          bgColor: "bg-green-50",
          borderColor: "border-green-200",
        };
      case "requires_reauth":
      case "needs_reauth":
        return {
          icon: AlertTriangle,
          label: "Needs Reauth",
          color: "text-yellow-600",
          bgColor: "bg-yellow-50",
          borderColor: "border-yellow-200",
        };
      case "error":
        return {
          icon: XCircle,
          label: "Error",
          color: "text-red-600",
          bgColor: "bg-red-50",
          borderColor: "border-red-200",
        };
      default:
        return {
          icon: AlertTriangle,
          label: status,
          color: "text-gray-600",
          bgColor: "bg-gray-50",
          borderColor: "border-gray-200",
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;
  const needsReauth = status === "requires_reauth" || status === "needs_reauth";
  const hasError = status === "error";

  return (
    <div className="relative inline-block">
      {/* Status Badge */}
      <button
        type="button"
        onClick={needsReauth && onReauth ? handleReauthClick : undefined}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${
          config.bgColor
        } ${config.borderColor} ${config.color} ${
          needsReauth && onReauth
            ? "cursor-pointer hover:opacity-80"
            : "cursor-default"
        } transition-opacity`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        disabled={!needsReauth || !onReauth}
      >
        <Icon className="w-3.5 h-3.5" />
        <span className="text-xs font-medium">{config.label}</span>
      </button>

      {/* Tooltip */}
      {showTooltip && (hasError || needsReauth) && (
        <div
          className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <div
            className={`rounded-lg border shadow-lg p-3 ${config.bgColor} ${config.borderColor}`}
          >
            <div className="flex items-start gap-2">
              <Icon
                className={`w-4 h-4 flex-shrink-0 mt-0.5 ${config.color}`}
              />
              <div className="flex-1">
                {needsReauth && (
                  <>
                    <p className="text-sm font-medium text-gray-900 mb-1">
                      Reconnection Required
                    </p>
                    <p className="text-xs text-gray-600">
                      {institutionName || "This account"} needs to be
                      reconnected to continue syncing data.
                    </p>
                    {onReauth && (
                      <p className="text-xs text-yellow-800 mt-2 font-medium">
                        Click this badge to reconnect →
                      </p>
                    )}
                  </>
                )}
                {hasError && errorMessage && (
                  <>
                    <p className="text-sm font-medium text-gray-900 mb-1">
                      Connection Error
                    </p>
                    <p className="text-xs text-gray-600">{errorMessage}</p>
                  </>
                )}
                {hasError && !errorMessage && (
                  <>
                    <p className="text-sm font-medium text-gray-900 mb-1">
                      Connection Error
                    </p>
                    <p className="text-xs text-gray-600">
                      Unable to sync data. Please try again or contact support.
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>
          {/* Tooltip Arrow */}
          <div
            className={`absolute top-full left-1/2 transform -translate-x-1/2 -mt-px`}
          >
            <div
              className={`w-2 h-2 rotate-45 ${config.bgColor} border-b border-r ${config.borderColor}`}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
}
