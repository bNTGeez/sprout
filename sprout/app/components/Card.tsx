import React from "react";

const Card = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="bg-white px-6 py-4 rounded-lg shadow-sm border border-gray-200 h-full w-full">
      {children}
    </div>
  );
};

export default Card;
