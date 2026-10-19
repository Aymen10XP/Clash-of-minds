import { useEffect, useState, type FormEvent } from 'react';
import { IonButton } from '@ionic/react';
import GameSubpage from '../../components/game/GameSubpage';
import { createQuestion, deactivateUser, fetchAdminUsers, type AdminUser } from '../../features/admin/api';
import { practiceTopics } from '../../features/practice/topics';
import { usePressNavigation } from '../../hooks/usePressNavigation';
import { appRoutes } from '../../routing/routes';
import './AdminConsole.css';

const emptyChoices = ['', '', '', ''];

const AdminConsole: React.FC = () => {
  const { goBackAfterPress } = usePressNavigation({ delay: 140, feedback: 'light' });
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [prompt, setPrompt] = useState('');
  const [topicSlug, setTopicSlug] = useState(practiceTopics[0].id);
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [explanation, setExplanation] = useState('');
  const [choices, setChoices] = useState([...emptyChoices]);
  const [correctChoiceIndex, setCorrectChoiceIndex] = useState(0);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const loadUsers = async () => {
    const response = await fetchAdminUsers();
    setUsers(response.users);
  };

  useEffect(() => {
    void loadUsers().catch((loadError) => setError(loadError instanceof Error ? loadError.message : 'Unable to load users.'));
  }, []);

  const submitQuestion = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');
    try {
      await createQuestion({ topicSlug, prompt, explanation, difficulty, choices, correctChoiceIndex, isActive: true });
      setPrompt('');
      setExplanation('');
      setChoices([...emptyChoices]);
      setCorrectChoiceIndex(0);
      setNotice('Question added and activated.');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Unable to add question.');
    } finally {
      setSaving(false);
    }
  };

  const updateChoice = (index: number, value: string) => {
    setChoices((current) => current.map((item, choiceIndex) => choiceIndex === index ? value : item));
  };

  const disableUser = async (user: AdminUser) => {
    if (!window.confirm(`Deactivate ${user.username}? They will no longer be able to sign in.`)) return;
    setError('');
    try {
      await deactivateUser(user.id);
      setUsers((current) => current.map((item) => item.id === user.id ? { ...item, isActive: false } : item));
      setNotice(`${user.username} was deactivated.`);
    } catch (deactivateError) {
      setError(deactivateError instanceof Error ? deactivateError.message : 'Unable to deactivate user.');
    }
  };

  return (
    <GameSubpage eyebrow="Staff access" title="Admin Console" onBack={() => goBackAfterPress(appRoutes.home)} className="admin-page">
      <div className="admin-layout">
        <section className="admin-panel">
          <h2>Add a quiz question</h2>
          <form className="admin-form" onSubmit={submitQuestion}>
            <label>Topic<select value={topicSlug} onChange={(event) => setTopicSlug(event.currentTarget.value)}>{practiceTopics.map((topic) => <option key={topic.id} value={topic.id}>{topic.title}</option>)}</select></label>
            <label>Difficulty<select value={difficulty} onChange={(event) => setDifficulty(event.currentTarget.value as typeof difficulty)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
            <label className="admin-form__wide">Question<textarea value={prompt} onChange={(event) => setPrompt(event.currentTarget.value)} required /></label>
            {choices.map((choice, index) => (
              <label className="admin-answer admin-form__wide" key={index}>
                <input type="radio" name="correct-answer" checked={correctChoiceIndex === index} onChange={() => setCorrectChoiceIndex(index)} aria-label={`Mark answer ${index + 1} correct`} />
                <span>Answer {index + 1}</span>
                <input value={choice} onChange={(event) => updateChoice(index, event.currentTarget.value)} required />
              </label>
            ))}
            <label className="admin-form__wide">Explanation (optional)<textarea value={explanation} onChange={(event) => setExplanation(event.currentTarget.value)} /></label>
            <IonButton className="admin-form__wide" type="submit" disabled={saving}>{saving ? 'Adding...' : 'Add and activate question'}</IonButton>
          </form>
        </section>

        <section className="admin-panel">
          <h2>User accounts</h2>
          <div className="admin-users">
            {users.map((user) => (
              <div className="admin-user" key={user.id}>
                <div><strong>{user.username}</strong><span>{user.email} · {user.country}{user.isStaff ? ' · Staff' : ''}</span></div>
                <IonButton size="small" color="danger" fill="outline" disabled={!user.isActive || user.isStaff} onClick={() => void disableUser(user)}>{user.isActive ? 'Deactivate' : 'Inactive'}</IonButton>
              </div>
            ))}
          </div>
        </section>
        {error && <p className="admin-message admin-message--error" role="alert">{error}</p>}
        {notice && <p className="admin-message" role="status">{notice}</p>}
      </div>
    </GameSubpage>
  );
};

export default AdminConsole;
