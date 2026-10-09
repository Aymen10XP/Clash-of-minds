import {
  bulbOutline,
  compassOutline,
  earthOutline,
  hardwareChipOutline,
  peopleOutline,
  shieldOutline,
} from 'ionicons/icons';

export interface PracticeTopic {
  id: string;
  title: string;
  description: string;
  era: string;
  icon: string;
}

export const practiceTopics: readonly PracticeTopic[] = [
  { id: 'ancient-civilizations', title: 'Ancient Civilizations', description: 'Empires, myths, rulers, and lost cities.', era: 'Origins', icon: earthOutline },
  { id: 'medieval-world', title: 'Medieval World', description: 'Kingdoms, scholars, trade, and conquest.', era: '500 to 1500', icon: shieldOutline },
  { id: 'revolutions', title: 'Age of Revolutions', description: 'Ideas and uprisings that reshaped nations.', era: '1600 to 1900', icon: peopleOutline },
  { id: 'inventions', title: 'Inventions', description: 'Discoveries that changed how humanity lives.', era: 'Ideas', icon: bulbOutline },
  { id: 'computing', title: 'Computing & AI', description: 'From early machines to intelligent systems.', era: 'Technology', icon: hardwareChipOutline },
  { id: 'mixed-knowledge', title: 'Across the Ages', description: 'A balanced challenge drawn from every archive.', era: 'Mixed', icon: compassOutline },
] as const;
