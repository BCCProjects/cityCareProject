import { useRouter } from "expo-router";
import { useMemo, useState } from "react";
import { FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";

import { ErrorState } from "@/components/feedback/ErrorState";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingState } from "@/components/feedback/LoadingState";
import { SelectField } from "@/components/form/SelectField";
import { Card } from "@/components/ui/Card";
import { Screen } from "@/components/ui/Screen";
import { useCategories } from "@/features/reference-data/hooks";
import { useReports } from "@/features/reports/hooks";
import { ListReportsParams } from "@/features/reports/api";
import { REPORT_STATUS_OPTIONS } from "@/features/reports/types";
import { formatDate } from "@/utils/format";

type StatusFilter = (typeof REPORT_STATUS_OPTIONS)[number]["value"] | "";

export default function ReportsTab() {
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [categoryFilter, setCategoryFilter] = useState<number | "">("");

  const { data: categoriesData } = useCategories();

  const queryParams = useMemo<ListReportsParams | undefined>(() => {
    const params: ListReportsParams = {};
    if (statusFilter) {
      params.status = statusFilter;
    }
    if (categoryFilter && typeof categoryFilter === "number") {
      params.category = categoryFilter;
    }
    return Object.keys(params).length ? params : undefined;
  }, [statusFilter, categoryFilter]);

  const { data, isLoading, isRefetching, refetch, error } = useReports(queryParams);

  const reports = data?.results ?? [];
  const isEmpty = reports.length === 0;

  const categoryItems =
    categoriesData?.map((category) => ({
      label: `${category.name} (${category.department.name})`,
      value: category.id,
    })) ?? [];

  const handleClearFilters = () => {
    setStatusFilter("");
    setCategoryFilter("");
    refetch();
  };

  return (
    <Screen scrollable={false}>
      <View style={styles.container}>
        <Text style={styles.headerTitle}>Minhas ocorrências</Text>
        <Text style={styles.headerSubtitle}>Acompanhe o andamento das suas solicitações.</Text>
        <View style={styles.filters}>
          <SelectField
            label="Status"
            items={REPORT_STATUS_OPTIONS.map((option) => ({
              label: option.label,
              value: option.value,
            }))}
            selectedValue={statusFilter}
            onValueChange={(value) => setStatusFilter(value as StatusFilter)}
            placeholder="Todos"
          />
          <SelectField
            label="Categoria"
            items={categoryItems}
            selectedValue={categoryFilter}
            onValueChange={(value) => setCategoryFilter(value as number | "")}
            placeholder="Todas"
          />
          <Pressable onPress={handleClearFilters}>
            <Text style={styles.clearFilters}>Limpar filtros</Text>
          </Pressable>
        </View>

        {error ? (
          <ErrorState message={error instanceof Error ? error.message : undefined} onRetry={() => refetch()} />
        ) : null}

        {isLoading ? (
          <LoadingState message="Carregando suas ocorrências..." />
        ) : (
          <FlatList
            data={reports}
            keyExtractor={(item) => String(item.id)}
            refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
            renderItem={({ item }) => (
              <Pressable
                onPress={() =>
                  router.push({
                    pathname: "/(app)/reports/[id]",
                    params: { id: String(item.id) },
                  })
                }
              >
                <Card>
                  <Text style={styles.reportTitle}>{item.title}</Text>
                  <Text style={styles.reportMeta}>
                    {item.category.name} • {formatDate(item.created_at)}
                  </Text>
                  <View style={styles.badgeRow}>
                    <View style={[styles.badge, styles.statusBadge]}>
                      <Text style={styles.badgeText}>{item.status}</Text>
                    </View>
                    <View style={[styles.badge, styles.priorityBadge]}>
                      <Text style={styles.badgeText}>Prioridade: {item.priority}</Text>
                    </View>
                  </View>
                  {item.tags.length ? (
                    <View style={styles.tagRow}>
                      {item.tags.map((tag) => (
                        <View key={tag.id} style={styles.tagChip}>
                          <Text style={styles.tagText}>{tag.name}</Text>
                        </View>
                      ))}
                    </View>
                  ) : null}
                </Card>
              </Pressable>
            )}
            ListEmptyComponent={
              <EmptyState
                title="Nenhuma ocorrência encontrada"
                subtitle="Crie uma nova ocorrência ou ajuste os filtros."
              />
            }
            contentContainerStyle={isEmpty ? [styles.listContent, styles.listEmptyContainer] : styles.listContent}
          />
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1e293b",
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 15,
    color: "#475569",
    marginBottom: 16,
  },
  filters: {
    marginBottom: 12,
    gap: 12,
  },
  clearFilters: {
    color: "#2563eb",
    fontWeight: "500",
    textAlign: "right",
    marginTop: 4,
  },
  reportTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#1e293b",
  },
  reportMeta: {
    marginTop: 4,
    color: "#64748b",
  },
  badgeRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 12,
  },
  badge: {
    borderRadius: 999,
    paddingVertical: 4,
    paddingHorizontal: 12,
  },
  statusBadge: {
    backgroundColor: "#e0f2fe",
  },
  priorityBadge: {
    backgroundColor: "#ede9fe",
  },
  badgeText: {
    color: "#0f172a",
    fontWeight: "600",
    fontSize: 13,
  },
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 12,
  },
  tagChip: {
    borderRadius: 999,
    backgroundColor: "#e2e8f0",
    paddingVertical: 4,
    paddingHorizontal: 10,
  },
  tagText: {
    color: "#475569",
    fontSize: 12,
  },
  listContent: {
    paddingBottom: 32,
  },
  listEmptyContainer: {
    flexGrow: 1,
    justifyContent: "center",
  },
});
