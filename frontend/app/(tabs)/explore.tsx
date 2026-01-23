import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Linking,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../contexts/LanguageContext';
import { colors } from '../../utils/colors';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import {
  eventService,
  placeService,
  accommodationService,
  itineraryService,
  favoriteService,
} from '../../services/api';

interface City {
  id: string;
  name: string;
}

export default function Explore() {
  const { t, language } = useLanguage();
  const router = useRouter();
  const [selectedCity, setSelectedCity] = useState<City | null>(null);
  const [activeSection, setActiveSection] = useState<string>('itineraries');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any[]>([]);
  const [favorites, setFavorites] = useState<any[]>([]);

  useEffect(() => {
    loadSelectedCity();
    loadFavorites();
  }, []);

  useEffect(() => {
    if (selectedCity) {
      loadData();
    }
  }, [selectedCity, activeSection]);

  async function loadSelectedCity() {
    const stored = await AsyncStorage.getItem('@LocalGuide:selectedCity');
    if (stored) {
      setSelectedCity(JSON.parse(stored));
    }
  }

  async function loadFavorites() {
    try {
      const favs = await favoriteService.getAll();
      setFavorites(favs);
    } catch (error) {
      console.error('Error loading favorites:', error);
    }
  }

  async function loadData() {
    setLoading(true);
    try {
      let result = [];
      switch (activeSection) {
        case 'events':
          result = await eventService.getAll(selectedCity!.id);
          break;
        case 'places':
          result = await placeService.getAll(selectedCity!.id);
          break;
        case 'accommodations':
          result = await accommodationService.getAll(selectedCity!.id);
          break;
        case 'itineraries':
          result = await itineraryService.getAll(selectedCity!.id);
          break;
      }
      setData(result);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }

  const isFavorite = (itemId: string) => {
    return favorites.some(
      (fav) => fav.item_id === itemId && fav.item_type === activeSection.slice(0, -1)
    );
  };

  const toggleFavorite = async (itemId: string) => {
    try {
      const itemType = activeSection === 'itineraries' ? 'itinerary' : activeSection.slice(0, -1);
      const existing = favorites.find(
        (fav) => fav.item_id === itemId && fav.item_type === itemType
      );

      if (existing) {
        await favoriteService.remove(existing.id);
        setFavorites(favorites.filter((f) => f.id !== existing.id));
      } else {
        const newFav = await favoriteService.add(itemType, itemId);
        setFavorites([...favorites, newFav]);
      }
    } catch (error: any) {
      Alert.alert(t('Erro', 'Error'), error.message);
    }
  };

  const openExternalLink = (link: string) => {
    Linking.openURL(link);
  };

  if (!selectedCity) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.emptyContainer}>
          <Ionicons name="location-outline" size={80} color={colors.gray} />
          <Text style={styles.emptyTitle}>
            {t('Nenhuma cidade selecionada', 'No city selected')}
          </Text>
          <Text style={styles.emptyText}>
            {t(
              'Volte para a tela inicial e selecione uma cidade',
              'Go back to home and select a city'
            )}
          </Text>
          <TouchableOpacity
            style={styles.emptyButton}
            onPress={() => router.push('/(tabs)')}
          >
            <Text style={styles.emptyButtonText}>
              {t('Selecionar Cidade', 'Select City')}
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const sections = [
    { key: 'itineraries', label: t('Itinerários', 'Itineraries'), icon: 'map' },
    { key: 'events', label: t('Eventos', 'Events'), icon: 'calendar' },
    { key: 'places', label: t('Lugares', 'Places'), icon: 'restaurant' },
    { key: 'accommodations', label: t('Hospedagem', 'Accommodation'), icon: 'bed' },
  ];

  const renderItem = (item: any) => {
    const name =
      item.name ||
      (language === 'pt' ? item.name_pt : item.name_en) ||
      item.name_pt ||
      item.name_en;
    const description =
      language === 'pt' ? item.description_pt : item.description_en || item.description_pt;

    return (
      <View key={item.id} style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.cardTitleContainer}>
            <Text style={styles.cardTitle}>{name}</Text>
            {item.tags && item.tags.length > 0 && (
              <View style={styles.tagsContainer}>
                {item.tags.slice(0, 2).map((tag: string, index: number) => (
                  <View key={index} style={styles.tag}>
                    <Text style={styles.tagText}>{tag}</Text>
                  </View>
                ))}
              </View>
            )}
          </View>
          <TouchableOpacity onPress={() => toggleFavorite(item.id)}>
            <Ionicons
              name={isFavorite(item.id) ? 'heart' : 'heart-outline'}
              size={24}
              color={isFavorite(item.id) ? colors.primary : colors.gray}
            />
          </TouchableOpacity>
        </View>

        <Text style={styles.cardDescription} numberOfLines={3}>
          {description}
        </Text>

        {activeSection === 'itineraries' && item.type && (
          <View style={styles.itineraryType}>
            <Ionicons name="compass" size={16} color={colors.secondary} />
            <Text style={styles.itineraryTypeText}>
              {item.type === 'aventureiro'
                ? t('Aventureiro', 'Adventurer')
                : item.type === 'cultural'
                ? t('Cultural', 'Cultural')
                : t('Chilling', 'Chilling')}
            </Text>
          </View>
        )}

        {item.external_links && (
          <View style={styles.linksContainer}>
            {item.external_links.google_maps && (
              <TouchableOpacity
                style={styles.linkButton}
                onPress={() => openExternalLink(item.external_links.google_maps)}
              >
                <Ionicons name="map" size={18} color={colors.white} />
                <Text style={styles.linkButtonText}>{t('Mapa', 'Map')}</Text>
              </TouchableOpacity>
            )}
            {item.external_links.instagram && (
              <TouchableOpacity
                style={[styles.linkButton, styles.instagramButton]}
                onPress={() => openExternalLink(item.external_links.instagram)}
              >
                <Ionicons name="logo-instagram" size={18} color={colors.white} />
                <Text style={styles.linkButtonText}>Instagram</Text>
              </TouchableOpacity>
            )}
            {item.external_links.website && (
              <TouchableOpacity
                style={[styles.linkButton, styles.websiteButton]}
                onPress={() => openExternalLink(item.external_links.website)}
              >
                <Ionicons name="globe" size={18} color={colors.white} />
                <Text style={styles.linkButtonText}>Website</Text>
              </TouchableOpacity>
            )}
            {item.external_links.airbnb && (
              <TouchableOpacity
                style={[styles.linkButton, styles.airbnbButton]}
                onPress={() => openExternalLink(item.external_links.airbnb)}
              >
                <Ionicons name="home" size={18} color={colors.white} />
                <Text style={styles.linkButtonText}>Airbnb</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.cityName}>{selectedCity.name}</Text>
          <Text style={styles.subtitle}>
            {t('Explore experiências locais', 'Explore local experiences')}
          </Text>
        </View>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.sectionsScroll}>
        {sections.map((section) => (
          <TouchableOpacity
            key={section.key}
            style={[
              styles.sectionButton,
              activeSection === section.key && styles.sectionButtonActive,
            ]}
            onPress={() => setActiveSection(section.key)}
          >
            <Ionicons
              name={section.icon as any}
              size={20}
              color={activeSection === section.key ? colors.white : colors.dark}
            />
            <Text
              style={[
                styles.sectionButtonText,
                activeSection === section.key && styles.sectionButtonTextActive,
              ]}
            >
              {section.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView contentContainerStyle={styles.content}>
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
          </View>
        ) : data.length === 0 ? (
          <View style={styles.emptyDataContainer}>
            <Ionicons name="search-outline" size={60} color={colors.gray} />
            <Text style={styles.emptyDataText}>
              {t('Nenhum resultado encontrado', 'No results found')}
            </Text>
          </View>
        ) : (
          data.map(renderItem)
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
  header: {
    padding: 24,
    paddingBottom: 16,
  },
  cityName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.dark,
  },
  subtitle: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: 4,
  },
  sectionsScroll: {
    paddingHorizontal: 24,
    marginBottom: 16,
  },
  sectionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: colors.lightGray,
    marginRight: 12,
  },
  sectionButtonActive: {
    backgroundColor: colors.primary,
  },
  sectionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.dark,
  },
  sectionButtonTextActive: {
    color: colors.white,
  },
  content: {
    padding: 24,
    paddingTop: 8,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  card: {
    backgroundColor: colors.white,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: colors.dark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  cardTitleContainer: {
    flex: 1,
    marginRight: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.dark,
    marginBottom: 8,
  },
  cardDescription: {
    fontSize: 14,
    color: colors.textLight,
    lineHeight: 20,
    marginBottom: 12,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tag: {
    backgroundColor: colors.accent,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  tagText: {
    fontSize: 11,
    color: colors.dark,
    fontWeight: '600',
  },
  itineraryType: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  itineraryTypeText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.secondary,
  },
  linksContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  linkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  instagramButton: {
    backgroundColor: '#E1306C',
  },
  websiteButton: {
    backgroundColor: colors.secondary,
  },
  airbnbButton: {
    backgroundColor: '#FF5A5F',
  },
  linkButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.white,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: colors.dark,
    marginTop: 24,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: colors.textLight,
    textAlign: 'center',
    marginBottom: 24,
  },
  emptyButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  emptyButtonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
  },
  emptyDataContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  emptyDataText: {
    fontSize: 16,
    color: colors.textLight,
    marginTop: 16,
  },
});