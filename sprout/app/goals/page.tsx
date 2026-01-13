"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plus, Target, Pencil, Trash2, ArchiveRestore } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { fetchGoals, createGoal, updateGoal, deleteGoal } from "@/lib/api";
import { GoalForm } from "../components/goals/GoalForm";
import { Toast, ToastType } from "../components/Toast";
import type {
  Goal,
  GoalCreateRequest,
  GoalUpdateRequest,
} from "@/app/types/goals";

export default function GoalsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string>("");
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: ToastType;
  } | null>(null);

  useEffect(() => {
    const getSession = async () => {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (session?.access_token) {
        setToken(session.access_token);
      } else {
        router.push("/login");
      }
      setIsLoadingAuth(false);
    };

    getSession();
  }, [router]);

  useEffect(() => {
    const loadGoals = async () => {
      if (!token) return;

      try {
        setIsLoading(true);
        // Fetch goals based on showArchived filter
        const goalsData = await fetchGoals(
          token,
          showArchived ? undefined : true
        );
        setGoals(goalsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load goals");
      } finally {
        setIsLoading(false);
      }
    };

    loadGoals();
  }, [token, showArchived]);

  const handleCreateGoal = async (data: GoalCreateRequest) => {
    try {
      await createGoal(token, data);
      setToast({
        message: "Goal created successfully!",
        type: "success",
      });
      setIsFormOpen(false);
      // Reload goals
      const goalsData = await fetchGoals(
        token,
        showArchived ? undefined : true
      );
      setGoals(goalsData);
    } catch (error) {
      setToast({
        message:
          error instanceof Error ? error.message : "Failed to create goal",
        type: "error",
      });
      throw error;
    }
  };

  const handleUpdateGoal = async (data: GoalUpdateRequest) => {
    if (!editingGoal) return;

    try {
      await updateGoal(token, editingGoal.id, data);
      setToast({
        message: "Goal updated successfully!",
        type: "success",
      });
      setIsFormOpen(false);
      setEditingGoal(null);
      // Reload goals
      const goalsData = await fetchGoals(
        token,
        showArchived ? undefined : true
      );
      setGoals(goalsData);
    } catch (error) {
      setToast({
        message:
          error instanceof Error ? error.message : "Failed to update goal",
        type: "error",
      });
      throw error;
    }
  };

  const handleDeleteGoal = async (goalId: number) => {
    if (
      !confirm(
        "Are you sure you want to delete this goal? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      await deleteGoal(token, goalId);
      setToast({
        message: "Goal deleted successfully!",
        type: "success",
      });
      // Reload goals
      const goalsData = await fetchGoals(
        token,
        showArchived ? undefined : true
      );
      setGoals(goalsData);
    } catch (error) {
      setToast({
        message:
          error instanceof Error ? error.message : "Failed to delete goal",
        type: "error",
      });
    }
  };

  const handleUnarchiveGoal = async (goalId: number) => {
    try {
      await updateGoal(token, goalId, { is_active: true });
      setToast({
        message: "Goal unarchived successfully!",
        type: "success",
      });
      // Reload goals
      const goalsData = await fetchGoals(
        token,
        showArchived ? undefined : true
      );
      setGoals(goalsData);
    } catch (error) {
      setToast({
        message:
          error instanceof Error ? error.message : "Failed to unarchive goal",
        type: "error",
      });
    }
  };

  const handleEditClick = (goal: Goal) => {
    setEditingGoal(goal);
    setIsFormOpen(true);
  };

  const handleAddClick = () => {
    setEditingGoal(null);
    setIsFormOpen(true);
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setEditingGoal(null);
  };

  if (isLoadingAuth || isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-lg shadow p-6 animate-pulse"
            >
              <div className="h-6 w-32 bg-gray-200 rounded mb-4"></div>
              <div className="h-4 w-24 bg-gray-100 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Goals</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track your savings goals and progress
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setShowArchived(!showArchived)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-2 ${
              showArchived
                ? "bg-gray-100 text-gray-700 hover:bg-gray-200"
                : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
            }`}
          >
            {showArchived ? (
              <>
                <ArchiveRestore className="w-4 h-4" />
                Show Active
              </>
            ) : (
              <>
                <ArchiveRestore className="w-4 h-4" />
                Show Archived
              </>
            )}
          </button>
          <button
            type="button"
            onClick={handleAddClick}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Goal
          </button>
        </div>
      </div>

      {/* Goals Grid */}
      {goals.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-gray-400 text-5xl mb-4">🎯</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {showArchived ? "No archived goals" : "No goals yet"}
          </h3>
          <p className="text-gray-500 mb-4">
            {showArchived
              ? "You don't have any archived goals"
              : "Create your first savings goal to track your progress"}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {goals.map((goal) => {
            const current = parseFloat(goal.current_amount);
            const target = parseFloat(goal.target_amount);
            const remaining = parseFloat(goal.remaining);
            const progressPercent = goal.progress_percent;

            return (
              <div
                key={goal.id}
                className={`bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow ${
                  !goal.is_active ? "opacity-75" : ""
                }`}
              >
                {/* Goal Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Target className="w-5 h-5 text-blue-600" />
                    <h3 className="text-lg font-semibold text-gray-900">
                      {goal.name}
                    </h3>
                  </div>
                  <div className="flex items-center gap-2">
                    {goal.is_met ? (
                      <span className="text-xs px-2 py-1 rounded bg-green-100 text-green-800">
                        Goal met
                      </span>
                    ) : goal.on_track !== null ? (
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          goal.on_track
                            ? "bg-green-100 text-green-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
                        {goal.on_track ? "On track" : "Behind"}
                      </span>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => handleEditClick(goal)}
                      className="text-gray-400 hover:text-blue-600 transition-colors"
                      title="Edit goal"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    {goal.is_active ? (
                      <button
                        type="button"
                        onClick={() => handleDeleteGoal(goal.id)}
                        className="text-gray-400 hover:text-red-600 transition-colors"
                        title="Delete goal"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleUnarchiveGoal(goal.id)}
                        className="text-gray-400 hover:text-green-600 transition-colors"
                        title="Unarchive goal"
                      >
                        <ArchiveRestore className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Progress */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Progress</span>
                    <span className="font-medium text-gray-900">
                      ${current.toFixed(2)} / ${target.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-blue-500 transition-all"
                      style={{ width: `${Math.min(progressPercent, 100)}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>{progressPercent.toFixed(1)}% complete</span>
                    <span>${remaining.toFixed(2)} to go</span>
                  </div>
                </div>

                {/* Target Date */}
                {goal.target_date && (
                  <div className="text-sm text-gray-600">
                    Target: {new Date(goal.target_date).toLocaleDateString()}
                  </div>
                )}

                {/* Monthly Contribution */}
                {goal.monthly_contribution && (
                  <div className="text-sm text-gray-600">
                    Monthly: ${parseFloat(goal.monthly_contribution).toFixed(2)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Goal Form Modal */}
      <GoalForm
        isOpen={isFormOpen}
        onClose={handleFormClose}
        goal={editingGoal}
        onSubmit={async (data) => {
          if (editingGoal) {
            await handleUpdateGoal(data as GoalUpdateRequest);
          } else {
            await handleCreateGoal(data as GoalCreateRequest);
          }
        }}
      />

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
