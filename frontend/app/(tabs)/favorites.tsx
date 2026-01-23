import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  Linking,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../contexts/LanguageContext';
import { colors } from '../../utils/colors';
import { Ionicons } from '@expo/vector-icons';
import {
  favoriteService,
  eventService,
  placeService,
  accommodationService,
  itineraryService,
} from '../../services/api';

export default function Favorites() {
  const { t, language } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState<any[]>([]);
  const [groupedFavorites, setGroupedFavorites] = useState<any>({});

  useEffect(() => {
    loadFavorites();
  }, []);

  async function loadFavorites() {
    setLoading(true);
    try {
      const favs = await favoriteService.getAll();
      
      // Load full data for each favorite
      const favoritesWithData = await Promise.all(
        favs.map(async (fav) => {
          let itemData = null;
          try {
            switch (fav.item_type) {
              case 'event':
                itemData = await eventService.getById(fav.item_id);
                break;
              case 'place':
                itemData = await placeService.getById(fav.item_id);
                break;
              case 'accommodation':
                itemData = await accommodationService.getById(fav.item_id);
                break;
              case 'itinerary':
                itemData = await itineraryService.getById(fav.item_id);
                break;
            }
          } catch (error) {
            console.error('Error loading favorite item:', error);
          }
          return { ...fav, data: itemData };
        })
      );

      // Group by type
      const grouped: any = {};
      favoritesWithData.forEach((fav) => {
        if (fav.data) {
          if (!grouped[fav.item_type]) {
            grouped[fav.item_type] = [];
          }
          grouped[fav.item_type].push(fav);
        }
      });

      setFavorites(favoritesWithData.filter((f) => f.data));
      setGroupedFavorites(grouped);
    } catch (error) {
      console.error('Error loading favorites:', error);
    } finally {
      setLoading(false);
    }
  }

  const removeFavorite = async (favoriteId: string) => {
    try {
      await favoriteService.remove(favoriteId);
      setFavorites(favorites.filter((f) => f.id !== favoriteId));
      // Reload to update grouped favorites
      loadFavorites();
    } catch (error: any) {
      Alert.alert(t('Erro', 'Error'), error.message);
    }
  };

  const openExternalLink = (link: string) => {
    Linking.openURL(link);
  };

  const renderFavoriteItem = (favorite: any) => {
    const item = favorite.data;
    if (!item) return null;

    const name =
      item.name ||
      (language === 'pt' ? item.name_pt : item.name_en) ||
      item.name_pt ||
      item.name_en;
    const description =
      language === 'pt' ? item.description_pt : item.description_en || item.description_pt;

    return (
      <View key={favorite.id} style={styles.card}>
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
          <TouchableOpacity onPress={() => removeFavorite(favorite.id)}>
            <Ionicons name="heart" size={24} color={colors.primary} />
          </TouchableOpacity>
        </View>

        <Text style={styles.cardDescription} numberOfLines={2}>
          {description}
        </Text>

        {item.external_links && (
          <View style={styles.linksContainer}>
            {item.external_links.google_maps && (
              <TouchableOpacity
                style={styles.linkButton}
                onPress={() => openExternalLink(item.external_links.google_maps)}
              >
                <Ionicons name="map" size={16} color={colors.white} />
                <Text style={styles.linkButtonText}>{t('Mapa', 'Map')}</Text>
              </TouchableOpacity>
            )}
            {item.external_links.instagram && (
              <TouchableOpacity
                style={[styles.linkButton, styles.instagramButton]}
                onPress={() => openExternalLink(item.external_links.instagram)}
              >
                <Ionicons name="logo-instagram" size={16} color={colors.white} />
              </TouchableOpacity>
            )}
            {item.external_links.website && (
              <TouchableOpacity
                style={[styles.linkButton, styles.websiteButton]}
                onPress={() => openExternalLink(item.external_links.website)}
              >
                <Ionicons name="globe" size={16} color={colors.white} />
              </TouchableOpacity>
            )}
          </View>
        )}
      </View>
    );
  };

  const getTypeTitle = (type: string) => {
    switch (type) {
      case 'event':
        return t('Eventos', 'Events');
      case 'place':
        return t('Lugares', 'Places');
      case 'accommodation':
        return t('Hospedagem', 'Accommodations');
      case 'itinerary':
        return t('Itinerários', 'Itineraries');
      default:
        return type;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'event':
        return 'calendar';
      case 'place':
        return 'restaurant';
      case 'accommodation':
        return 'bed';
      case 'itinerary':
        return 'map';
      default:
        return 'star';
    }
  };

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
      <View style={styles.header}>
        <Text style={styles.title}>{t('Meus Favoritos', 'My Favorites')}</Text>
        <Text style={styles.subtitle}>
          {favorites.length} {t('items salvos', 'saved items')}
        </Text>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {favorites.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons name="heart-outline" size={80} color={colors.gray} />
            <Text style={styles.emptyTitle}>
              {t('Nenhum favorito ainda', 'No favorites yet')}
            </Text>
            <Text style={styles.emptyText}>
              {t(
                'Explore lugares e adicione aos favoritos',
                'Explore places and add them to favorites'
              )}
            </Text>
          </View>
        ) : (
          Object.keys(groupedFavorites).map((type) => (
            <View key={type} style={styles.section}>
              <View style={styles.sectionHeader}>
                <Ionicons name={getTypeIcon(type) as any} size={24} color={colors.primary} />
                <Text style={styles.sectionTitle}>{getTypeTitle(type)}</Text>
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{groupedFavorites[type].length}</Text>
                </View>
              </View>
              {groupedFavorites[type].map(renderFavoriteItem)}
            </View>
          ))
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
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.dark,
  },
  subtitle: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: 4,
  },
  content: {
    padding: 24,
    paddingTop: 8,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: colors.dark,
    marginTop: 24,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 16,
    color: colors.textLight,
    textAlign: 'center',
  },
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.dark,
    flex: 1,
  },
  badge: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 2,
    minWidth: 24,
    alignItems: 'center',
  },
  badgeText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: colors.white,
  },
  card: {
    backgroundColor: colors.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: colors.dark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  cardTitleContainer: {
    flex: 1,
    marginRight: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.dark,
    marginBottom: 6,
  },
  cardDescription: {
    fontSize: 13,
    color: colors.textLight,
    lineHeight: 18,
    marginBottom: 10,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tag: {
    backgroundColor: colors.accent,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  tagText: {
    fontSize: 10,
    color: colors.dark,
    fontWeight: '600',
  },
  linksContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  linkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.primary,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
  },
  instagramButton: {
    backgroundColor: '#E1306C',
  },
  websiteButton: {
    backgroundColor: colors.secondary,
  },
  linkButtonText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.white,
  },
});