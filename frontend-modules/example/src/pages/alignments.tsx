import "@r4pm/components/styles.css";
import { Box, LoadingOverlay, Tabs, Select, Stack } from "@mantine/core";
import { defineModuleRoute, useCurrentOcel } from "@ocelescope/core";
import type { LogAlignments } from "@r4pm/components";
import { AlignmentListViewer, Theme } from "@r4pm/components";
import { useGetAlignments, useObjectTypes } from "../api/example";
import { ResourceSelect } from "@ocelescope/resources";
import { useState } from "react";
import { keepPreviousData } from "@tanstack/react-query";

const AlignmentComponent = ({
  ocelId,
  objectType
}: {
  ocelId: string;
  objectType: string;
}) => {
  const [resourceId, setResourceId] = useState<string | null>(null)
  const { data, isPending } = useGetAlignments(ocelId, { object_type: objectType, resource_id:resourceId}, {query:{placeholderData:keepPreviousData}});

return (
  <Box pos="relative" h="100%" style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
    <LoadingOverlay visible={isPending || !data} />
    <ResourceSelect label="Petri Net" type="PetriNet" value={resourceId} onChange={(newResourceId) => setResourceId(newResourceId as string)}/>
    <Box style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
      {data && <AlignmentListViewer data={data as LogAlignments} />}
    </Box>
  </Box>
);
}


const Alignment = () => {
  const { id } = useCurrentOcel();
  const { data: objectTypes } = useObjectTypes(id, undefined, { query: { enabled: !!id } });

  if (!id || !objectTypes) {
    return <LoadingOverlay visible />;
  }

  const [firstObjectType, ...otherObjectTypes] = objectTypes;
  if (!firstObjectType) {
    return null;
  }

  return (<Theme style={{ height: "100%", minHeight: 0 }}>
    {otherObjectTypes.length > 0 ? (
      <Tabs defaultValue={firstObjectType} keepMounted={false} h={"100%"}>
        <Stack h="100%" gap={"xs"}>
          <Tabs.List>
            {objectTypes.map((objectType) => (
              <Tabs.Tab key={objectType} value={objectType}>
                {objectType}
              </Tabs.Tab>
            ))}
          </Tabs.List>
          {objectTypes.map((objectType) => (
            <Tabs.Panel key={objectType} value={objectType} pt="md" flex={1}>
              <AlignmentComponent ocelId={id} objectType={objectType} />
            </Tabs.Panel>
          ))}</Stack>
      </Tabs>) : <AlignmentComponent ocelId={id} objectType={firstObjectType} />}
  </Theme>
  );
}

export const alignmentspage = defineModuleRoute({
  component: Alignment,
  label: "example",
  name: "example",
  requiresOcel: true,
});

