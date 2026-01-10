import { Building2, Plus } from "lucide-react";

export default function EmptyAccountsState() {
  return (
    <div className="text-center py-16">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
        <Building2 className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        No accounts connected
      </h3>
      <p className="text-gray-500 mb-6 max-w-sm mx-auto">
        Link your bank to get started tracking your finances automatically.
      </p>
      <button className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
        <Plus className="w-4 h-4" />
        Connect Bank Account
      </button>
    </div>
  );
}
