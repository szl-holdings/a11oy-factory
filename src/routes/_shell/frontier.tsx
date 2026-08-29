import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/app-shell";
import { FrontierWorkbench } from "@/components/frontier-workbench";
import { OrganWorkbench } from "@/components/organ-workbench";
import { OwnerOrderBanner } from "@/components/owner-order-banner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ORGANS } from "@/lib/organs";

export const Route = createFileRoute("/_shell/frontier")({
  component: FrontierPage,
});

function FrontierPage() {
  return (
    <Page
      kicker="Frontier organs"
      title="N1–N25 is live."
      lede="Twenty-five category organs run in this factory: front end, back end, hashed receipts. Not 25 public Spaces. GPU tune stays UNAVAILABLE."
    >
      <OwnerOrderBanner />
      <p className="mt-4 font-mono text-xs text-subtle">{ORGANS.length} organs · honesty LIVE · public admission false</p>
      <div className="mt-8">
        <Tabs defaultValue="organs">
          <TabsList className="flex w-full flex-wrap justify-start">
            <TabsTrigger value="organs">N1–N25 organs</TabsTrigger>
            <TabsTrigger value="packet6">Packet 6 compiler</TabsTrigger>
          </TabsList>
          <TabsContent value="organs" className="mt-6">
            <OrganWorkbench />
          </TabsContent>
          <TabsContent value="packet6" className="mt-6">
            <FrontierWorkbench />
          </TabsContent>
        </Tabs>
      </div>
    </Page>
  );
}
