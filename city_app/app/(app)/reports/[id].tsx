import { useLocalSearchParams } from "expo-router";

import { ErrorState } from "@/components/feedback/ErrorState";
import { LoadingState } from "@/components/feedback/LoadingState";
import { Card } from "@/components/ui/Card";
import { Screen } from "@/components/ui/Screen";
import { useReportDetail } from "@/features/reports/hooks";
import { formatDate } from "@/utils/format";

import { Pressable } from "react-native";
import {View, Text, Image, ScrollView, Linking, StyleSheet,} from "react-native";

export default function ReportDetailScreen() {
  const params = useLocalSearchParams();
  const reportId = params.id ? Number(params.id) : null;

  const { data, isLoading, error, refetch } = useReportDetail(reportId);

  if (isLoading) {
    return <LoadingState message="Carregando detalhes..." />;
  }

  if (error) {
    return (
      <Screen scrollable={false}>
        <ErrorState message={error instanceof Error ? error.message : undefined} onRetry={refetch} />
      </Screen>
    );
  }

  if (!data) {
    return (
      <Screen scrollable={false}>
        <ErrorState message="Ocorrência não encontrada." />
      </Screen>
    );
  }

  return (
    <Screen scrollable={false}>
      <ScrollView contentContainerStyle={styles.container}>
        <Card>
          <Text style={styles.title}>{data.title}</Text>
          <Text style={styles.meta}>
            {data.category.name} • Departamento {data.department.name}
          </Text>
          <View style={styles.badgeRow}>
            <View style={[styles.badge, styles.statusBadge]}>
              <Text style={styles.badgeText}>{data.status}</Text>
            </View>
            <View style={[styles.badge, styles.priorityBadge]}>
              <Text style={styles.badgeText}>Prioridade: {data.priority}</Text>
            </View>
          </View>
          <Text style={styles.sectionTitle}>Descrição</Text>
          <Text style={styles.description}>{data.description}</Text>
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Endereço</Text>
          <Text style={styles.infoText}>{data.address}</Text>
          <Text style={styles.infoText}>
            Bairro {data.neighborhood} - Coordenadas {data.latitude}, {data.longitude}
          </Text>
          <Text style={styles.infoText}>Organização responsável: {data.organization}</Text>
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Andamento</Text>
          <Text style={styles.infoText}>
            Criado em {formatDate(data.created_at)} - Última atualização {formatDate(data.last_status_at)}
          </Text>
          {data.denied_reason ? (
            <>
              <Text style={styles.sectionTitle}>Motivo do indeferimento</Text>
              <Text style={styles.description}>{data.denied_reason}</Text>
            </>
          ) : null}
        </Card>

        {data.tags.length ? (
          <Card>
            <Text style={styles.sectionTitle}>Tags</Text>
            <View style={styles.tagRow}>
              {data.tags.map((tag) => (
                <View key={tag.id} style={styles.tagChip}>
                  <Text style={styles.tagText}>{tag.name}</Text>
                </View>
              ))}
            </View>
          </Card>
        ) : null}

       {Array.isArray(data.attachments) && data.attachments.length > 0 ? (
        <Card>
          <Text style={styles.sectionTitle}>Anexos</Text>
          <View style={styles.attachmentList}>
            {data.attachments.map((attachment) => (
              <Pressable
                key={attachment.id}
                onPress={() => Linking.openURL(attachment.file)}
              >
                <Image
                  source={{ uri: attachment.file }}
                  style={styles.attachmentImage}
                  resizeMode="cover"
                />
              </Pressable>
            ))}
          </View>
        </Card>
       ) : null}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingBottom: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1f2937",
    marginBottom: 6,
  },
  meta: {
    color: "#475569",
    marginBottom: 12,
  },
  badgeRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 16,
  },
  badge: {
    borderRadius: 999,
    paddingVertical: 6,
    paddingHorizontal: 14,
  },
  badgeText: {
    fontWeight: "600",
    color: "#0f172a",
  },
  statusBadge: {
    backgroundColor: "#e0f2fe",
  },
  priorityBadge: {
    backgroundColor: "#ede9fe",
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1e293b",
    marginTop: 12,
    marginBottom: 6,
  },
  description: {
    color: "#334155",
    lineHeight: 20,
  },
  infoText: {
    color: "#475569",
    marginBottom: 6,
  },
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  tagChip: {
    backgroundColor: "#e2e8f0",
    borderRadius: 999,
    paddingVertical: 4,
    paddingHorizontal: 10,
  },
  tagText: {
    color: "#475569",
  },
  attachmentList: {
    gap: 8,
  },
  attachmentLink: {
    color: "#2563eb",
    textDecorationLine: "underline",
  },
attachmentImage: {
  width: 300,   
  height: 200,  
  borderRadius: 10,
  marginBottom: 10,
}
});