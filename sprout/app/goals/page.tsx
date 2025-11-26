import Card from "@/app/components/Card";

const page = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div>
        <h1 className="mx-4 my-6 text-2xl font-bold text-gray-900">Goals</h1>
      </div>
      <div className="">
        <Card>
          <h2>Active Goals</h2>
        </Card>
      </div>
    </div>
  );
};

export default page;
