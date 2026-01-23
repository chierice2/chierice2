import React, { createContext, useState, useContext, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

type Language = 'pt' | 'en';

interface LanguageContextData {
  language: Language;
  setLanguage: (lang: Language) => Promise<void>;
  t: (ptText: string, enText: string) => string;
}

const LanguageContext = createContext<LanguageContextData>({} as LanguageContextData);

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [language, setLanguageState] = useState<Language>('pt');

  async function setLanguage(lang: Language) {
    setLanguageState(lang);
    await AsyncStorage.setItem('@LocalGuide:language', lang);
  }

  function t(ptText: string, enText: string) {
    return language === 'pt' ? ptText : enText;
  }

  React.useEffect(() => {
    loadLanguage();
  }, []);

  async function loadLanguage() {
    const stored = await AsyncStorage.getItem('@LocalGuide:language');
    if (stored) {
      setLanguageState(stored as Language);
    }
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