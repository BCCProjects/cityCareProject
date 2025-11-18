import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import * as Location from "expo-location";
import GoogleMapReact from "google-map-react";

import { Button } from "@/components/ui/Button";
import { env } from "@/config/env";

type Region = {
  latitude: number;
  longitude: number;
  latitudeDelta: number;
  longitudeDelta: number;
};

type PlaceSuggestion = {
  placeId: string;
  primaryText: string;
  secondaryText?: string;
  description: string;
};

type LocationPickerProps = {
  latitude: string;
  longitude: string;
  onChange: (value: { latitude: string; longitude: string; address?: string; neighborhood?: string }) => void;
  error?: string;
};

const DEFAULT_REGION: Region = {
  latitude: -23.55052,
  longitude: -46.63331,
  latitudeDelta: 0.08,
  longitudeDelta: 0.08,
};

const formatCoordinate = (value: number) => value.toFixed(6);
const generateSessionToken = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;

const Marker = () => (
  <View style={styles.marker}>
    <View style={styles.markerDot} />
  </View>
);

export function LocationPicker({ latitude, longitude, onChange, error }: LocationPickerProps) {
  const [region, setRegion] = useState<Region>(() => {
    const lat = Number(latitude);
    const lng = Number(longitude);
    if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
      return {
        latitude: lat,
        longitude: lng,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      };
    }
    return DEFAULT_REGION;
  });
  const [isLocating, setIsLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [searchText, setSearchText] = useState("");
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const sessionTokenRef = useRef(generateSessionToken());

  const hasApiKey = useMemo(() => Boolean(env.googleMapsApiKey), []);

  const updateLocation = useCallback(
    (lat: number, lng: number, extra?: { address?: string; neighborhood?: string }) => {
      setRegion((current) => ({
        ...current,
        latitude: lat,
        longitude: lng,
      }));
      onChange({
        latitude: formatCoordinate(lat),
        longitude: formatCoordinate(lng),
        ...extra,
      });
      if (extra?.address) {
        setSearchText(extra.address);
      }
    },
    [onChange],
  );

  const requestDeviceLocation = useCallback(async () => {
    try {
      setIsLocating(true);
      setLocationError(null);
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== Location.PermissionStatus.GRANTED) {
        setLocationError("Permissão de localização não concedida.");
        return;
      }

      const position = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      updateLocation(position.coords.latitude, position.coords.longitude);
    } catch (err) {
      console.warn("Failed to get device location", err);
      setLocationError("Não foi possível obter sua localização.");
    } finally {
      setIsLocating(false);
    }
  }, [updateLocation]);

  useEffect(() => {
    if (!latitude || !longitude) {
      requestDeviceLocation();
    }
  }, [latitude, longitude, requestDeviceLocation]);

  const extractNeighborhood = (components?: { long_name: string; types: string[] }[]) => {
    if (!components) {
      return undefined;
    }
    const match = components.find((component) =>
      component.types.some((type) => type === "sublocality" || type === "sublocality_level_1" || type === "neighborhood"),
    );
    return match?.long_name;
  };

  const fetchPlaceDetails = useCallback(
    async (placeId: string) => {
      if (!hasApiKey) {
        return null;
      }
      const url = new URL("https://maps.googleapis.com/maps/api/place/details/json");
      url.searchParams.set("place_id", placeId);
      url.searchParams.set("fields", "formatted_address,geometry,address_component");
      url.searchParams.set("language", "pt-BR");
      url.searchParams.set("key", env.googleMapsApiKey);
      url.searchParams.set("sessiontoken", sessionTokenRef.current);

      const response = await fetch(url.toString());
      const payload = await response.json();
      if (payload.status !== "OK" || !payload.result) {
        throw new Error(payload.error_message ?? "Não foi possível obter os detalhes do local.");
      }
      return payload.result as {
        formatted_address?: string;
        geometry?: { location?: { lat: number; lng: number } };
        address_components?: { long_name: string; types: string[] }[];
      };
    },
    [hasApiKey],
  );

  const handleSelectSuggestion = useCallback(
    async (suggestion: PlaceSuggestion) => {
      try {
        setIsSearching(true);
        setSearchError(null);
        const details = await fetchPlaceDetails(suggestion.placeId);
        if (!details?.geometry?.location) {
          throw new Error("Local selecionado não possui coordenadas.");
        }
        updateLocation(details.geometry.location.lat, details.geometry.location.lng, {
          address: details.formatted_address ?? suggestion.description,
          neighborhood: extractNeighborhood(details.address_components),
        });
        setSuggestions([]);
        setSearchText(details.formatted_address ?? suggestion.description);
        sessionTokenRef.current = generateSessionToken();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Não foi possível selecionar o local.";
        setSearchError(message);
      } finally {
        setIsSearching(false);
      }
    },
    [fetchPlaceDetails, updateLocation],
  );

  useEffect(() => {
    if (!hasApiKey) {
      setSuggestions([]);
      return;
    }
    const trimmed = searchText.trim();
    if (trimmed.length < 3) {
      setSuggestions([]);
      setSearchError(null);
      return;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(async () => {
      try {
        setIsSearching(true);
        setSearchError(null);
        const url = new URL("https://maps.googleapis.com/maps/api/place/autocomplete/json");
        url.searchParams.set("input", trimmed);
        url.searchParams.set("language", "pt-BR");
        url.searchParams.set("components", "country:br");
        url.searchParams.set("key", env.googleMapsApiKey);
        url.searchParams.set("sessiontoken", sessionTokenRef.current);

        const response = await fetch(url.toString(), { signal: controller.signal });
        const payload = await response.json();
        if (payload.status === "ZERO_RESULTS") {
          setSuggestions([]);
          return;
        }
        if (payload.status !== "OK") {
          throw new Error(payload.error_message ?? `Falha ao buscar endereços (${payload.status}).`);
        }

        const mapped: PlaceSuggestion[] = (payload.predictions ?? []).map((prediction: any) => ({
          placeId: prediction.place_id,
          primaryText: prediction.structured_formatting?.main_text ?? prediction.description,
          secondaryText: prediction.structured_formatting?.secondary_text,
          description: prediction.description,
        }));
        setSuggestions(mapped);
      } catch (err) {
        if (controller.signal.aborted) {
          return;
        }
        const message = err instanceof Error ? err.message : "Falha ao buscar locais no Google Maps.";
        setSearchError(message);
      } finally {
        setIsSearching(false);
      }
    }, 350);

    return () => {
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [searchText, hasApiKey]);

  const markerCoordinate = useMemo(() => {
    const lat = Number(latitude);
    const lng = Number(longitude);
    if (Number.isNaN(lat) || Number.isNaN(lng)) {
      return null;
    }
    return { latitude: lat, longitude: lng };
  }, [latitude, longitude]);

  const mapCenter = useMemo(
    () => ({
      lat: region.latitude,
      lng: region.longitude,
    }),
    [region.latitude, region.longitude],
  );

  const handleMapClick = useCallback(
    ({ lat, lng }: { lat: number; lng: number }) => {
      updateLocation(lat, lng);
    },
    [updateLocation],
  );

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Localização</Text>

      {hasApiKey ? (
        <View style={styles.autocompleteContainer}>
          <TextInput
            style={styles.autocompleteInput}
            value={searchText}
            onChangeText={setSearchText}
            placeholder="Buscar endereço ou ponto de referência"
            placeholderTextColor="#94a3b8"
            autoCorrect={false}
            autoCapitalize="none"
          />
          {isSearching ? <ActivityIndicator style={styles.autocompleteSpinner} /> : null}
          {suggestions.length > 0 ? (
            <View style={styles.autocompleteList}>
              {suggestions.map((suggestion) => (
                <Pressable
                  key={suggestion.placeId}
                  style={styles.autocompleteItem}
                  onPress={() => handleSelectSuggestion(suggestion)}
                >
                  <Text style={styles.autocompletePrimary}>{suggestion.primaryText}</Text>
                  {suggestion.secondaryText ? (
                    <Text style={styles.autocompleteSecondary}>{suggestion.secondaryText}</Text>
                  ) : null}
                </Pressable>
              ))}
            </View>
          ) : null}
          {searchError ? <Text style={styles.helperError}>{searchError}</Text> : null}
        </View>
      ) : (
        <Text style={styles.helper}>
          Configure a variável EXPO_PUBLIC_GOOGLE_MAPS_SECRET_KEY para habilitar buscas de endereço.
        </Text>
      )}

      {hasApiKey ? (
        <View style={styles.mapWrapper}>
          <GoogleMapReact
            bootstrapURLKeys={{ key: env.googleMapsApiKey }}
            center={mapCenter}
            defaultZoom={11}
            onClick={handleMapClick}
          >
            {markerCoordinate ? <Marker lat={markerCoordinate.latitude} lng={markerCoordinate.longitude} /> : null}
          </GoogleMapReact>
        </View>
      ) : (
        <View style={[styles.mapWrapper, styles.mapFallback]}>
          <Text style={styles.mapFallbackText}>
            O mapa interativo não está disponível sem uma chave de API do Google Maps. Utilize o campo de busca para
            definir a localização.
          </Text>
        </View>
      )}

      <View style={styles.coordinatesRow}>
        <View style={styles.coordinateCard}>
          <Text style={styles.coordinateLabel}>Latitude</Text>
          <Text style={styles.coordinateValue}>{latitude || "—"}</Text>
        </View>
        <View style={styles.coordinateCard}>
          <Text style={styles.coordinateLabel}>Longitude</Text>
          <Text style={styles.coordinateValue}>{longitude || "—"}</Text>
        </View>
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}
      {locationError ? <Text style={styles.helperError}>{locationError}</Text> : null}

      <Button title="Usar minha localização atual" onPress={requestDeviceLocation} loading={isLocating} />

      {!hasApiKey ? (
        <View style={styles.warningBox}>
          <Text style={styles.warningText}>
            Adicione um Google Maps API Key válido para desbloquear sugestões e assegurar que o mapa use dados atualizados.
          </Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 18,
  },
  label: {
    fontWeight: "600",
    marginBottom: 6,
    color: "#1e293b",
    fontSize: 15,
  },
  helper: {
    marginBottom: 8,
    color: "#475569",
  },
  helperError: {
    marginBottom: 12,
    color: "#dc2626",
  },
  autocompleteContainer: {
    borderWidth: 1,
    borderColor: "#cbd5f5",
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginBottom: 8,
    backgroundColor: "#ffffff",
    zIndex: 2,
  },
  autocompleteInput: {
    fontSize: 16,
    minHeight: 42,
    color: "#0f172a",
  },
  autocompleteSpinner: {
    position: "absolute",
    right: 12,
    top: 12,
  },
  autocompleteList: {
    borderWidth: 1,
    borderColor: "#cbd5f5",
    borderRadius: 12,
    marginTop: 8,
    backgroundColor: "#ffffff",
    zIndex: 3,
    elevation: 4,
    overflow: "hidden",
  },
  autocompleteItem: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  autocompletePrimary: {
    fontSize: 15,
    fontWeight: "600",
    color: "#0f172a",
  },
  autocompleteSecondary: {
    marginTop: 2,
    fontSize: 13,
    color: "#64748b",
  },
  mapWrapper: {
    height: 240,
    borderRadius: 16,
    overflow: "hidden",
    marginBottom: 12,
  },
  mapFallback: {
    backgroundColor: "#e2e8f0",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
  },
  mapFallbackText: {
    color: "#475569",
    textAlign: "center",
  },
  coordinatesRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 12,
  },
  coordinateCard: {
    flex: 1,
    backgroundColor: "#f1f5f9",
    borderRadius: 12,
    padding: 12,
  },
  coordinateLabel: {
    fontSize: 12,
    color: "#475569",
    marginBottom: 4,
  },
  coordinateValue: {
    fontSize: 16,
    fontWeight: "600",
    color: "#0f172a",
  },
  error: {
    color: "#dc2626",
    marginBottom: 12,
  },
  warningBox: {
    marginTop: 12,
    padding: 12,
    borderRadius: 12,
    backgroundColor: "#fef3c7",
  },
  warningText: {
    color: "#92400e",
    fontSize: 13,
  },
  marker: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "rgba(37, 99, 235, 0.2)",
    alignItems: "center",
    justifyContent: "center",
    transform: [{ translateY: -16 }],
  },
  markerDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: "#2563eb",
    borderWidth: 2,
    borderColor: "#ffffff",
  },
});

