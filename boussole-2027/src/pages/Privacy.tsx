import { LLM_ENABLED } from '../ui/LlmPanel';

export function PrivacyPage() {
  return (
    <article className="prose">
      <h1>Confidentialité</h1>
      <p>
        Vos opinions politiques sont des <strong>données sensibles</strong> au sens de l'article 9 du règlement général sur la protection des données (RGPD).
        Boussole 2027 a été conçue pour ne jamais les collecter.
      </p>
      <h2>Ce qui se passe quand vous répondez</h2>
      <ul>
        <li><strong>Tout le calcul se fait dans votre navigateur.</strong> Vos réponses ne sont envoyées à aucun serveur, ni pendant le questionnaire ni après.</li>
        <li><strong>Aucun cookie, aucun traceur, aucune mesure d'audience.</strong> Les polices de caractères sont hébergées avec l'application : aucune requête n'est faite vers un service tiers.</li>
        <li><strong>Rien n'est conservé par défaut.</strong> Vos réponses restent dans l'onglet ouvert et disparaissent à sa fermeture.</li>
        <li><strong>Sauvegarde locale facultative.</strong> Si vous cochez « Conserver ma progression sur cet appareil », vos réponses sont enregistrées dans le stockage local de votre navigateur (localStorage), sur cet appareil uniquement. Le bouton « Effacer mes réponses » les supprime. Évitez cette option sur un ordinateur partagé.</li>
        <li><strong>Statistiques.</strong> La version actuelle ne produit aucune statistique, même agrégée. Si une mesure agrégée devait être proposée un jour, elle serait facultative, soumise à votre accord explicite préalable et anonymisée.</li>
      </ul>
      <h2>Exports et partage</h2>
      <ul>
        <li>Les exports PNG et PDF sont fabriqués par votre navigateur et enregistrés sur votre appareil.</li>
        <li>Le lien de partage, facultatif, contient uniquement vos scores arrondis par axe (jamais vos réponses) après le signe « # » de l'adresse ; cette partie n'est pas transmise au serveur qui héberge le site. Toute personne qui reçoit le lien peut en revanche lire ces scores.</li>
      </ul>
      <h2>Commentaire par IA (option)</h2>
      <p>
        {LLM_ENABLED
          ? 'Cette version propose, à la fin des résultats, un commentaire rédigé par un modèle d\'IA. Il n\'est déclenché que si vous cochez la case d\'accord : seuls vos scores arrondis par axe sont alors envoyés à notre serveur, qui les transmet au fournisseur du modèle (Anthropic) sans les conserver. Vos réponses ne sont jamais envoyées.'
          : 'Cette option est désactivée dans la présente version : aucune donnée n\'est envoyée à un service d\'intelligence artificielle.'}
      </p>
      <h2>Vos droits</h2>
      <p>
        Comme l'application ne collecte pas de données personnelles, il n'existe pas de fichier vous concernant côté serveur. Vous gardez la maîtrise complète des données stockées
        localement : vous pouvez les effacer depuis l'application ou en vidant les données du site dans votre navigateur.
      </p>
    </article>
  );
}
