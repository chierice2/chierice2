import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { colors } from '../../utils/colors';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

export default function Profile() {
  const { user, signOut } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const router = useRouter();

  const handleSignOut = () => {
    Alert.alert(
      t('Sair', 'Sign Out'),
      t('Tem certeza que deseja sair?', 'Are you sure you want to sign out?'),
      [
        {
          text: t('Cancelar', 'Cancel'),
          style: 'cancel',
        },
        {
          text: t('Sair', 'Sign Out'),
          style: 'destructive',
          onPress: async () => {
            await signOut();
            router.replace('/');
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View style={styles.avatarContainer}>
            <Text style={styles.avatarText}>{user?.name.charAt(0).toUpperCase()}</Text>
          </View>
          <Text style={styles.name}>{user?.name}</Text>
          <Text style={styles.email}>{user?.email}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {t('Preferências', 'Preferences')}
          </Text>

          <View style={styles.card}>
            <View style={styles.settingItem}>
              <View style={styles.settingLeft}>
                <Ionicons name="language" size={24} color={colors.primary} />
                <Text style={styles.settingText}>
                  {t('Idioma', 'Language')}
                </Text>
              </View>
              <View style={styles.languageButtons}>
                <TouchableOpacity
                  style={[
                    styles.langButton,
                    language === 'pt' && styles.langButtonActive,
                  ]}
                  onPress={() => setLanguage('pt')}
                >
                  <Text
                    style={[
                      styles.langButtonText,
                      language === 'pt' && styles.langButtonTextActive,
                    ]}
                  >
                    PT
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.langButton,
                    language === 'en' && styles.langButtonActive,
                  ]}
                  onPress={() => setLanguage('en')}
                >
                  <Text
                    style={[
                      styles.langButtonText,
                      language === 'en' && styles.langButtonTextActive,
                    ]}
                  >
                    EN
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {t('Sobre', 'About')}
          </Text>

          <View style={styles.card}>
            <TouchableOpacity style={styles.settingItem}>
              <View style={styles.settingLeft}>
                <Ionicons name="information-circle" size={24} color={colors.secondary} />
                <Text style={styles.settingText}>
                  {t('Versão do App', 'App Version')}
                </Text>
              </View>
              <Text style={styles.settingValue}>1.0.0</Text>
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity style={styles.signOutButton} onPress={handleSignOut}>
          <Ionicons name="log-out-outline" size={20} color={colors.white} />
          <Text style={styles.signOutButtonText}>
            {t('Sair', 'Sign Out')}
          </Text>
        </TouchableOpacity>

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            {t(
              'Feito com ❤️ para viajantes',
              'Made with ❤️ for travelers'
            )}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: 24,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  avatarContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 40,
    fontWeight: 'bold',
    color: colors.white,
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.dark,
    marginBottom: 4,
  },
  email: {
    fontSize: 16,
    color: colors.textLight,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.dark,
    marginBottom: 12,
  },
  card: {
    backgroundColor: colors.white,
    borderRadius: 12,
    shadowColor: colors.dark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  settingText: {
    fontSize: 16,
    color: colors.dark,
    fontWeight: '500',
  },
  settingValue: {
    fontSize: 16,
    color: colors.textLight,
  },
  languageButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  langButton: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.lightGray,
    backgroundColor: colors.white,
  },
  langButtonActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  langButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.dark,
  },
  langButtonTextActive: {
    color: colors.white,
  },
  signOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: colors.error,
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 16,
  },
  signOutButtonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
  },
  footer: {
    alignItems: 'center',
    marginTop: 40,
  },
  footerText: {
    fontSize: 14,
    color: colors.textLight,
  },
});