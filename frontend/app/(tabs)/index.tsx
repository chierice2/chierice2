import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../contexts/LanguageContext';
import { useAuth } from '../../contexts/AuthContext';
import { colors } from '../../utils/colors';
import { Ionicons } from '@expo/vector-icons';
import { cityService, seedService } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';

interface City {
  id: string;
  name: string;
  slug: string;
  description_pt: string;
  description_en: string;
  image_base64: string | null;
}

export default function Home() {
  const { t, language } = useLanguage();
  const { user } = useAuth();
  const router = useRouter();
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCity, setSelectedCity] = useState<City | null>(null);

  useEffect(() => {
    loadCities();
    loadSelectedCity();
  }, []);

  async function loadCities() {
    try {
      const data = await cityService.getAll();
      
      // If no cities, seed the database
      if (data.length === 0) {
        await seedService.seed();
        const newData = await cityService.getAll();
        setCities(newData);
      } else {
        setCities(data);
      }
    } catch (error) {
      console.error('Error loading cities:', error);
      Alert.alert(
        t('Erro', 'Error'),
        t('Erro ao carregar cidades', 'Error loading cities')
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadSelectedCity() {
    const stored = await AsyncStorage.getItem('@LocalGuide:selectedCity');
    if (stored) {
      setSelectedCity(JSON.parse(stored));
    }
  }

  async function handleCitySelect(city: City) {
    setSelectedCity(city);
    await AsyncStorage.setItem('@LocalGuide:selectedCity', JSON.stringify(city));
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>
              {t('Olá', 'Hello')}, {user?.name}!
            </Text>
            <Text style={styles.subtitle}>
              {t('Para onde vamos hoje?', 'Where are we going today?')}
            </Text>
          </View>
          <Ionicons name="airplane" size={32} color={colors.primary} />
        </View>

        {selectedCity && (
          <View style={styles.selectedCityBanner}>
            <View style={styles.selectedCityContent}>
              <Ionicons name="location" size={20} color={colors.primary} />
              <View style={styles.selectedCityText}>
                <Text style={styles.selectedCityLabel}>
                  {t('Cidade Selecionada', 'Selected City')}
                </Text>
                <Text style={styles.selectedCityName}>{selectedCity.name}</Text>
              </View>
            </View>
            <TouchableOpacity onPress={() => router.push('/explore')}>
              <Ionicons name="chevron-forward" size={24} color={colors.primary} />
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {t('Escolha sua cidade', 'Choose your city')}
          </Text>
          
          <View style={styles.citiesGrid}>
            {cities.map((city) => (
              <TouchableOpacity
                key={city.id}
                style={[
                  styles.cityCard,
                  selectedCity?.id === city.id && styles.cityCardSelected,
                ]}
                onPress={() => handleCitySelect(city)}
              >
                <View style={styles.cityIconContainer}>
                  <Ionicons
                    name="location"
                    size={40}
                    color={selectedCity?.id === city.id ? colors.white : colors.primary}
                  />
                </View>
                <Text
                  style={[
                    styles.cityName,
                    selectedCity?.id === city.id && styles.cityNameSelected,
                  ]}
                >
                  {city.name}
                </Text>
                <Text
                  style={[
                    styles.cityDescription,
                    selectedCity?.id === city.id && styles.cityDescriptionSelected,
                  ]}
                  numberOfLines={2}
                >
                  {language === 'pt' ? city.description_pt : city.description_en}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {selectedCity && (
          <TouchableOpacity
            style={styles.exploreButton}
            onPress={() => router.push('/explore')}
          >
            <Text style={styles.exploreButtonText}>
              {t('Explorar ', 'Explore ')} {selectedCity.name}
            </Text>
            <Ionicons name="arrow-forward" size={20} color={colors.white} />
          </TouchableOpacity>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: 24,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  greeting: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.dark,
  },
  subtitle: {
    fontSize: 16,
    color: colors.textLight,
    marginTop: 4,
  },
  selectedCityBanner: {
    backgroundColor: colors.accent,
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  selectedCityContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  selectedCityText: {
    gap: 2,
  },
  selectedCityLabel: {
    fontSize: 12,
    color: colors.dark,
    fontWeight: '600',
  },
  selectedCityName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.dark,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.dark,
    marginBottom: 16,
  },
  citiesGrid: {
    gap: 16,
  },
  cityCard: {
    backgroundColor: colors.white,
    borderRadius: 16,
    padding: 20,
    borderWidth: 2,
    borderColor: colors.lightGray,
  },
  cityCardSelected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  cityIconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: colors.light,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  cityName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.dark,
    marginBottom: 4,
  },
  cityNameSelected: {
    color: colors.white,
  },
  cityDescription: {
    fontSize: 14,
    color: colors.textLight,
  },
  cityDescriptionSelected: {
    color: colors.white,
    opacity: 0.9,
  },
  exploreButton: {
    backgroundColor: colors.secondary,
    paddingVertical: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 8,
  },
  exploreButtonText: {
    color: colors.white,
    fontSize: 18,
    fontWeight: '600',
  },
});