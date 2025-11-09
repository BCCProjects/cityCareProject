import * as ImagePicker from "expo-image-picker";
import { useRouter } from "expo-router";
import { useMemo, useState } from "react";
import { Alert, Image, ScrollView, StyleSheet, Text, View } from "react-native";

import { ErrorMessage } from "@/components/form/ErrorMessage";
import { InputField } from "@/components/form/InputField";
import { LocationPicker } from "@/components/form/LocationPicker";
import { SelectField } from "@/components/form/SelectField";
import { ChipSelector } from "@/components/form/ChipSelector";
import { Button } from "@/components/ui/Button";
import { Screen } from "@/components/ui/Screen";
import { env } from "@/config/env";
import { useDepartments, useCategories, useTags } from "@/features/reference-data/hooks";
import { useCreateReport } from "@/features/reports/hooks";
import { REPORT_PRIORITY_OPTIONS } from "@/features/reports/types";

type Attachment = {
  uri: string;
  name: string;
  type: string;
};

export default function NewReportScreen() {
  const router = useRouter();
  const [departmentId, setDepartmentId] = useState<number | "">("");
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [priority, setPriority] = useState<"BAIXO" | "MODERADO" | "ALTO">("MODERADO");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [address, setAddress] = useState("");
  const [neighborhood, setNeighborhood] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [selectedTags, setSelectedTags] = useState<number[]>([]);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);

  const createReportMutation = useCreateReport();
  const { data: departmentsData } = useDepartments();
  const { data: categoriesData } = useCategories(typeof departmentId === "number" ? departmentId : undefined);
  const { data: tagsData } = useTags();

  const departmentItems =
    departmentsData?.map((department) => ({
      value: department.id,
      label: department.name,
    })) ?? [];

  const categoryItems =
    categoriesData?.map((category) => ({
      value: category.id,
      label: `${category.name} (${category.department.name})`,
    })) ?? [];

  const tagItems =
    tagsData?.map((tag) => ({
      id: tag.id,
      label: tag.name,
    })) ?? [];

  const handleToggleTag = (id: number) => {
    setSelectedTags((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  };

  const handlePickAttachment = async () => {
    if (attachments.length >= env.maxAttachments) {
      Alert.alert("Anexos", `Limite de ${env.maxAttachments} imagens atingido.`);
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsMultipleSelection: false,
      quality: 0.7,
    });

    if (result.canceled || !result.assets?.length) {
      return;
    }

    const asset = result.assets[0];
    const name = asset.fileName ?? `anexo-${attachments.length + 1}.jpg`;
    const type = asset.mimeType ?? "image/jpeg";

    setAttachments((current) => [...current, { uri: asset.uri, name, type }]);
  };

  const handleRemoveAttachment = (uri: string) => {
    setAttachments((current) => current.filter((item) => item.uri !== uri));
  };

  const validateForm = () => {
    if (!title || !description || !address || !neighborhood || !categoryId) {
      setErrorMessage("Preencha todos os campos obrigatórios.");
      return false;
    }
    if (!latitude || !longitude) {
      setLocationError("Selecione uma localização no mapa.");
      setErrorMessage("Preencha todos os campos obrigatórios.");
      return false;
    }
    if (title.length < 10) {
      setErrorMessage("O título deve ter pelo menos 10 caracteres.");
      return false;
    }
    if (Number.isNaN(Number(latitude)) || Number.isNaN(Number(longitude))) {
      setLocationError("Selecione uma localização válida.");
      setErrorMessage("Informe coordenadas válidas.");
      return false;
    }
    setErrorMessage(null);
    setLocationError(null);
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      const payload = {
        category_id: categoryId as number,
        title,
        description,
        priority,
        address,
        neighborhood,
        latitude,
        longitude,
        tag_ids: selectedTags,
        attachments,
      };
      const report = await createReportMutation.mutateAsync(payload);
      Alert.alert("Sucesso", "Ocorrência criada com sucesso!");
      router.push({
        pathname: "/(app)/reports/[id]",
        params: { id: String(report.id) },
      });
      setTitle("");
      setDescription("");
      setAddress("");
      setNeighborhood("");
      setLatitude("");
      setLongitude("");
      setCategoryId("");
      setDepartmentId("");
      setAttachments([]);
      setSelectedTags([]);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Falha ao criar ocorrência.";
    setErrorMessage(message);
  }
};

  const handleLocationChange = (value: { latitude: string; longitude: string; address?: string; neighborhood?: string }) => {
    setLatitude(value.latitude);
    setLongitude(value.longitude);
    if (value.address && !address) {
      setAddress(value.address);
    }
    if (value.neighborhood && !neighborhood) {
      setNeighborhood(value.neighborhood);
    }
  };

  const hintTags = useMemo(
    () =>
      selectedTags.length > 0
        ? `${selectedTags.length} tag(s) selecionada(s)`
        : "Selecione tags que ajudem a identificar a ocorrência.",
    [selectedTags],
  );

  return (
    <Screen scrollable={false}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Nova ocorrência</Text>
        <Text style={styles.subtitle}>Descreva com clareza para acelerar o atendimento.</Text>

        <ErrorMessage message={errorMessage} />

        <SelectField
          label="Departamento"
          items={departmentItems}
          selectedValue={departmentId}
          onValueChange={(value) => {
            setDepartmentId(value as number | "");
            setCategoryId("");
          }}
          placeholder="Selecione o departamento"
        />

        <SelectField
          label="Categoria"
          items={categoryItems}
          selectedValue={categoryId}
          onValueChange={(value) => setCategoryId(value as number | "")}
          placeholder="Selecione a categoria"
        />

        <SelectField
          label="Prioridade"
          items={REPORT_PRIORITY_OPTIONS.map((option) => ({
            label: option.label,
            value: option.value,
          }))}
          selectedValue={priority}
          onValueChange={(value) => setPriority(value as typeof priority)}
          placeholder="Defina a prioridade"
        />

        <InputField label="Título" value={title} onChangeText={setTitle} placeholder="Buraco na rua principal" />
        <InputField
          label="Descrição"
          value={description}
          multiline
          numberOfLines={4}
          onChangeText={setDescription}
          placeholder="Descreva a situação, horários e impacto"
          style={styles.multilineInput}
        />
        <InputField label="Endereço" value={address} onChangeText={setAddress} placeholder="Rua Exemplo, 123" />
        <InputField
          label="Bairro"
          value={neighborhood}
          onChangeText={setNeighborhood}
          placeholder="Centro"
        />
        <LocationPicker latitude={latitude} longitude={longitude} onChange={handleLocationChange} error={locationError ?? undefined} />

        <ChipSelector label="Tags" items={tagItems} selectedIds={selectedTags} onToggle={handleToggleTag} helperText={hintTags} />

        <View style={styles.attachmentHeader}>
          <Text style={styles.label}>Anexos</Text>
          <Text style={styles.helper}>Até {env.maxAttachments} imagens (JPG, PNG, WebP)</Text>
        </View>

        <View style={styles.attachmentRow}>
          {attachments.map((attachment) => (
            <View key={attachment.uri} style={styles.attachmentPreview}>
              <Image source={{ uri: attachment.uri }} style={styles.attachmentImage} />
              <Text style={styles.removeAttachment} onPress={() => handleRemoveAttachment(attachment.uri)}>
                Remover
              </Text>
            </View>
          ))}
        </View>

        <Button title="Adicionar imagem" onPress={handlePickAttachment} />

        <Button
          title="Registrar ocorrência"
          onPress={handleSubmit}
          loading={createReportMutation.isPending}
          disabled={createReportMutation.isPending}
        />
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
    color: "#1e293b",
  },
  subtitle: {
    marginTop: 6,
    marginBottom: 16,
    fontSize: 15,
    color: "#475569",
  },
  multilineInput: {
    minHeight: 120,
    textAlignVertical: "top",
  },
  row: {
    flexDirection: "row",
    gap: 12,
  },
  column: {
    flex: 1,
  },
  attachmentHeader: {
    marginTop: 12,
    marginBottom: 8,
  },
  label: {
    fontWeight: "600",
    color: "#1e293b",
  },
  helper: {
    marginTop: 4,
    fontSize: 12,
    color: "#64748b",
  },
  attachmentRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  attachmentPreview: {
    width: 110,
    height: 110,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "#e2e8f0",
    alignItems: "center",
    justifyContent: "center",
  },
  attachmentImage: {
    width: "100%",
    height: "100%",
  },
  removeAttachment: {
    position: "absolute",
    bottom: 6,
    fontSize: 12,
    color: "#ffffff",
    backgroundColor: "rgba(15, 23, 42, 0.7)",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 999,
  },
});
