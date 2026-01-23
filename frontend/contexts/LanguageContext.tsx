import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const translations = {
  pt: {
    // Welcome
    hello: 'Olá',
    welcome: 'Seu guia para experiências locais',
    signIn: 'Entrar',
    signUp: 'Criar Conta',
    
    // Auth
    welcomeBack: 'Bem-vindo de volta!',
    signInToContinue: 'Faça login para continuar',
    createAccount: 'Criar Conta',
    signUpToStart: 'Cadastre-se para começar',
    email: 'Email',
    password: 'Senha',
    name: 'Nome',
    fullName: 'Seu nome completo',
    yourEmail: 'seu@email.com',
    yourPassword: 'Sua senha',
    minChars: 'Mínimo 6 caracteres',
    alreadyHaveAccount: 'Já tem uma conta?',
    noAccount: 'Não tem uma conta?',
    
    // Errors
    error: 'Erro',
    fillAllFields: 'Por favor, preencha todos os campos',
    passwordMinLength: 'A senha deve ter pelo menos 6 caracteres',
    loginError: 'Erro ao fazer login',
    registrationError: 'Erro ao criar conta',
    tryAgain: 'Tente novamente',
    
    // Home
    whereToday: 'Para onde vamos hoje?',
    selectedCity: 'Cidade Selecionada',
    chooseCity: 'Escolha sua cidade',
    explore: 'Explorar',
    
    // Explore
    exploreLocal: 'Explore experiências locais',
    itineraries: 'Itinerários',
    events: 'Eventos',
    places: 'Lugares',
    accommodation: 'Hospedagem',
    noResults: 'Nenhum resultado encontrado',
    noCitySelected: 'Nenhuma cidade selecionada',
    goBackSelectCity: 'Volte para a tela inicial e selecione uma cidade',
    selectCity: 'Selecionar Cidade',
    
    // Itinerary types
    adventurer: 'Aventureiro',
    cultural: 'Cultural',
    chilling: 'Chilling',
    
    // Actions
    map: 'Mapa',
    
    // Favorites
    myFavorites: 'Meus Favoritos',
    savedItems: 'items salvos',
    noFavorites: 'Nenhum favorito ainda',
    exploreFavorites: 'Explore lugares e adicione aos favoritos',
    
    // Profile
    preferences: 'Preferências',
    language: 'Idioma',
    about: 'Sobre',
    appVersion: 'Versão do App',
    signOut: 'Sair',
    confirmSignOut: 'Tem certeza que deseja sair?',
    cancel: 'Cancelar',
    madeWithLove: 'Feito com ❤️ para viajantes',
    
    // Loading
    loading: 'Carregando...',
    signingIn: 'Entrando...',
    creating: 'Criando...',
  },
  en: {
    // Welcome
    hello: 'Hello',
    welcome: 'Your guide for local experiences',
    signIn: 'Sign In',
    signUp: 'Sign Up',
    
    // Auth
    welcomeBack: 'Welcome back!',
    signInToContinue: 'Sign in to continue',
    createAccount: 'Create Account',
    signUpToStart: 'Sign up to get started',
    email: 'Email',
    password: 'Password',
    name: 'Name',
    fullName: 'Your full name',
    yourEmail: 'your@email.com',
    yourPassword: 'Your password',
    minChars: 'Minimum 6 characters',
    alreadyHaveAccount: 'Already have an account?',
    noAccount: "Don't have an account?",
    
    // Errors
    error: 'Error',
    fillAllFields: 'Please fill all fields',
    passwordMinLength: 'Password must be at least 6 characters',
    loginError: 'Login error',
    registrationError: 'Registration error',
    tryAgain: 'Try again',
    
    // Home
    whereToday: 'Where are we going today?',
    selectedCity: 'Selected City',
    chooseCity: 'Choose your city',
    explore: 'Explore',
    
    // Explore
    exploreLocal: 'Explore local experiences',
    itineraries: 'Itineraries',
    events: 'Events',
    places: 'Places',
    accommodation: 'Accommodation',
    noResults: 'No results found',
    noCitySelected: 'No city selected',
    goBackSelectCity: 'Go back to home and select a city',
    selectCity: 'Select City',
    
    // Itinerary types
    adventurer: 'Adventurer',
    cultural: 'Cultural',
    chilling: 'Chilling',
    
    // Actions
    map: 'Map',
    
    // Favorites
    myFavorites: 'My Favorites',
    savedItems: 'saved items',
    noFavorites: 'No favorites yet',
    exploreFavorites: 'Explore places and add them to favorites',
    
    // Profile
    preferences: 'Preferences',
    language: 'Language',
    about: 'About',
    appVersion: 'App Version',
    signOut: 'Sign Out',
    confirmSignOut: 'Are you sure you want to sign out?',
    cancel: 'Cancel',
    madeWithLove: 'Made with ❤️ for travelers',
    
    // Loading
    loading: 'Loading...',
    signingIn: 'Signing in...',
    creating: 'Creating...',
  },
};

type Language = 'pt' | 'en';
type TranslationKey = keyof typeof translations.pt;

interface LanguageContextData {
  language: Language;
  setLanguage: (lang: Language) => Promise<void>;
  t: (key: TranslationKey) => string;
}

const LanguageContext = createContext<LanguageContextData | null>(null);

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [language, setLanguageState] = useState<Language>('pt');

  useEffect(() => {
    loadLanguage();
  }, []);

  async function loadLanguage() {
    try {
      const stored = await AsyncStorage.getItem('@LocalGuide:language');
      if (stored && (stored === 'pt' || stored === 'en')) {
        setLanguageState(stored);
      }
    } catch (error) {
      console.error('Error loading language:', error);
    }
  }

  async function setLanguage(lang: Language) {
    setLanguageState(lang);
    try {
      await AsyncStorage.setItem('@LocalGuide:language', lang);
    } catch (error) {
      console.error('Error saving language:', error);
    }
  }

  function t(key: TranslationKey): string {
    return translations[language][key] || key;
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
