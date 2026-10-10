import {
  useId,
  useMemo,
  useState,
  type FormEvent,
  type FocusEvent,
  type KeyboardEvent,
} from 'react';
import { IonIcon, IonInput, IonItem, IonLabel, IonList, IonNote } from '@ionic/react';
import { checkmarkOutline, flagOutline } from 'ionicons/icons';
import { countries, type CountryOption } from '../../features/auth/countries';
import { playUiFeedback } from '../../lib/uiFeedback';
import './CountryCombobox.css';

const CountryCombobox: React.FC = () => {
  const listboxId = useId();
  const [query, setQuery] = useState('');
  const [selectedCountry, setSelectedCountry] = useState<CountryOption | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const matchingCountries = useMemo(() => {
    const searchTerm = query.trim().toLocaleLowerCase();

    if (!searchTerm || selectedCountry?.name === query) {
      return countries;
    }

    return countries.filter(
      (country) =>
        country.name.toLocaleLowerCase().includes(searchTerm) ||
        country.code.toLocaleLowerCase().startsWith(searchTerm),
    );
  }, [query, selectedCountry]);

  const selectCountry = (country: CountryOption) => {
    setQuery(country.name);
    setSelectedCountry(country);
    setIsOpen(false);
    setActiveIndex(0);
    playUiFeedback('light');
  };

  const updateQuery = (nextQuery: string) => {
    setQuery(nextQuery);
    setSelectedCountry(null);
    setActiveIndex(0);
    setIsOpen(true);
  };

  const handleInput = (event: FormEvent<HTMLIonInputElement>) => {
    updateQuery(event.currentTarget.value?.toString() ?? '');
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLIonInputElement>) => {
    if (event.key === 'Escape') {
      setIsOpen(false);
      return;
    }

    if (!matchingCountries.length) {
      return;
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setIsOpen(true);
      setActiveIndex((currentIndex) => (currentIndex + 1) % matchingCountries.length);
      return;
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setIsOpen(true);
      setActiveIndex(
        (currentIndex) => (currentIndex - 1 + matchingCountries.length) % matchingCountries.length,
      );
      return;
    }

    if (event.key === 'Enter' && isOpen) {
      event.preventDefault();
      selectCountry(matchingCountries[activeIndex]);
    }
  };

  const handleBlur = (event: FocusEvent<HTMLDivElement>) => {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      setIsOpen(false);
    }
  };

  return (
    <div className="country-combobox" onBlur={handleBlur}>
      <IonInput
        className="auth-input country-combobox__input"
        fill="outline"
        labelPlacement="stacked"
        label="Country"
        placeholder="Start typing a country"
        autocomplete="country-name"
        value={query}
        aria-autocomplete="list"
        aria-controls={listboxId}
        aria-expanded={isOpen}
        aria-activedescendant={
          isOpen && matchingCountries.length
            ? `${listboxId}-option-${matchingCountries[activeIndex].code}`
            : undefined
        }
        onFocus={() => setIsOpen(true)}
        onIonFocus={() => setIsOpen(true)}
        onInput={handleInput}
        onIonInput={(event) => updateQuery(event.detail.value ?? '')}
        onKeyDown={handleKeyDown}
        required
      >
        <IonIcon icon={flagOutline} slot="start" aria-hidden="true" />
      </IonInput>

      <input type="hidden" name="country" value={selectedCountry?.code ?? ''} />

      {isOpen && (
        <IonList
          className="country-combobox__menu"
          id={listboxId}
          role="listbox"
          aria-label="Countries"
          lines="none"
        >
          {matchingCountries.length ? (
            matchingCountries.map((country, index) => (
              <IonItem
                className={`country-combobox__option${index === activeIndex ? ' is-active' : ''}`}
                id={`${listboxId}-option-${country.code}`}
                key={country.code}
                button
                detail={false}
                lines="none"
                  role="option"
                  aria-label={`${country.name} ${country.code}`}
                aria-selected={selectedCountry?.code === country.code}
                onPointerDown={(event) => event.preventDefault()}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => selectCountry(country)}
              >
                <IonLabel>{country.name}</IonLabel>
                <IonNote className="country-combobox__code" slot="end">
                  {country.code}
                </IonNote>
                {selectedCountry?.code === country.code && (
                  <IonIcon icon={checkmarkOutline} slot="end" aria-hidden="true" />
                )}
              </IonItem>
            ))
          ) : (
            <IonItem className="country-combobox__empty" lines="none">
              <IonLabel>No countries match that search.</IonLabel>
            </IonItem>
          )}
        </IonList>
      )}
    </div>
  );
};

export default CountryCombobox;
