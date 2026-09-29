import type { Dataset } from '../domain/load';
import { OPENNESS_WEIGHTS } from '../engine/indices';
import { CONFIDENCE_WEIGHT, MIN_CODED_AXES, SALIENCE_MAX, SALIENCE_MIN } from '../engine/matching';
import { BOOTSTRAP_DRAWS, MIN_EFFECTIVE_ITEMS } from '../engine/scoring';
import { frDate } from '../ui/DataBanner';

export function MethodologyPage({ data }: { data: Dataset }) {
  const count = (id: string) => data.questions.filter((q) => q.primaryAxis === id).length;
  const rev = (id: string) => data.questions.filter((q) => q.primaryAxis === id && q.type !== 'allocation' && q.reversed).length;
  const anchored = data.questions.filter((q) => q.sourceMeasure?.length).length;
  const coded = data.candidates.filter((c) => Object.values(c.positions).some((p) => p?.value !== null)).length;
  return (
    <article className="prose">
      <h1>Méthodologie</h1>
      <p className="section">
        <strong>Boussole 2027 est un outil de réflexion, pas une consigne de vote.</strong> Son objet est d'aider chacun·e à préciser sa propre orientation, à
        connaître les traditions intellectuelles qui la fondent et les objections qu'elle rencontre. La comparaison avec les candidat·es est indicative.
        Données candidat·es : état des connaissances au <strong>{frDate(data.meta.dataDate)}</strong>. Version {data.meta.version}.
      </p>

      <h2>1. Les axes</h2>
      <p>
        Dix axes principaux et cinq secondaires sont mesurés, dont le mode de changement (réformiste ↔ révolutionnaire), ajouté avec la version 2 du questionnaire.
        Trois axes optionnels (genre et famille, technique, rapport à l'histoire nationale) sont prévus mais ne sont pas mesurés dans cette version. Les intitulés des pôles reprennent la grille du fichier de référence des programmes (fichier 01).
      </p>
      <table>
        <thead><tr><th scope="col">Code</th><th scope="col">Axe</th><th scope="col">Pôle −100</th><th scope="col">Pôle +100</th><th scope="col">Items</th><th scope="col">Inversés</th></tr></thead>
        <tbody>
          {data.axes.map((a) => (
            <tr key={a.id}>
              <th scope="row">{a.id}</th><td>{a.label}{a.enabled ? '' : ' (optionnel, non mesuré)'}</td><td>{a.poleMinus}</td><td>{a.polePlus}</td>
              <td>{a.enabled ? count(a.id) : '—'}</td><td>{a.enabled ? rev(a.id) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Reformulations et facettes (fichier 01, §5)</h3>
      <ul>
        <li><strong>« Racisme / xénophobie » devient « Altérité »</strong> (fermeture ethno-nationale ↔ ouverture / égalitarisme antiraciste). Appliqué à une personne ou à un·e candidat·e, le premier intitulé serait un jugement moral et un risque juridique ; les candidat·es sont codé·es sur leurs mesures (immigration, nationalité, droits des étrangers). Pour l'utilisateur·ice, certains items s'inspirent de travaux de psychologie sociale (racisme symbolique, dominance sociale, autoritarisme) sans jamais attribuer d'étiquette.</li>
        <li><strong>Identité</strong> : « communautariste » s'entend au sens philosophique du <em>communitarianism</em> (Taylor, Sandel, MacIntyre) : primauté des appartenances, qu'elles soient nationales, religieuses ou minoritaires.</li>
        <li><strong>Religion</strong> : une facette distincte mesure la conception de la laïcité (libérale ou stricte), car une même mesure peut procéder d'un anticléricalisme républicain ou d'un attachement identitaire.</li>
        <li><strong>Gouvernance mondiale</strong> : deux facettes distinguent le recours à la force et le multilatéralisme, pour ne pas confondre interventionnisme multilatéral et unilatéral.</li>
        <li><strong>Environnement</strong> : une facette mesure la place du nucléaire, qui relève des moyens et non de l'intensité de l'engagement écologique.</li>
        <li><strong>Gouvernance</strong> : un gouvernement faible n'est pas synonyme d'État de droit ; l'axe mesure l'attachement aux règles qui encadrent le pouvoir, indépendamment de l'économie.</li>
      </ul>

      <h2>2. Les questions</h2>
      <p>
        {data.groups.length} blocs réunissent chacun un contexte (une mesure débattue, une situation concrète) et 4 affirmations qui couvrent des positions différentes
        plutôt que deux pôles, soit {data.questions.filter((q) => q.type === 'likert').length} affirmations. Chacune reçoit sa propre réponse : pas du tout d'accord, plutôt pas d'accord,
        neutre, plutôt d'accord, tout à fait d'accord, ou « je ne sais pas », qui exclut l'affirmation du calcul.{' '}
        {data.questions.filter((q) => q.type === 'choice').length} questions à choix proposent 5 à 7 options (plus « aucune de ces réponses ») : elles ouvrent l'éventail au-delà
        de l'opposition entre démocratie libérale et autoritarisme (démocratie directe ou des conseils, anarchisme, pouvoir national-autoritaire, technocratie).{' '}
        {data.questions.filter((q) => q.type === 'allocation').length} répartitions de 10 points complètent l'ensemble ; les deux dernières, sur les priorités, pondèrent la comparaison avec les candidat·es.
      </p>
      <p>
        Deux paires de blocs posent la même question dans deux contextes : l'Union européenne telle qu'elle est et telle que vous la souhaiteriez ; un gouvernement
        du camp opposé et un gouvernement de votre camp. Chaque axe principal compte au moins 8 affirmations principales dont au moins 3 dans le sens du pôle « moins »,
        chaque axe secondaire au moins 5 dont 2. {anchored} affirmations reformulent une mesure réelle d'un programme, sans nommer de candidat·e.
        Le vocabulaire en usage dans le débat (« lutte des classes », « grand remplacement », « assistanat »…) apparaît seulement dans une affirmation que le camp qui l'emploie
        pourrait signer, et il est expliqué dans le mode Apprendre ; l'outil décrit une adhésion, il ne qualifie pas la personne. Un linter vérifie automatiquement
        longueur (≤ 30 mots), absence de double négation et de noms de candidat·es, explication du vocabulaire marqué, équilibre des inversions et existence des références.
      </p>

      <h2>3. Calcul des scores</h2>
      <p>
        Réponse Likert r ∈ {'{'}−2, −1, 0, +1, +2{'}'}, poids w de l'item sur l'axe (signe = pôle favorisé par l'accord). Score de l'axe a :
      </p>
      <p className="formula">S<sub>a</sub> = 100 × Σ<sub>i</sub> w<sub>i,a</sub> · r<sub>i</sub> ⁄ (2 × Σ<sub>i</sub> |w<sub>i,a</sub>|), sur les items répondus, dans [−100 ; +100].</p>
      <ul>
        <li>Question à choix : l'option retenue compte comme un accord net (contribution 2 × w, maximum 2 × le plus grand |w| des options) ; « aucune de ces réponses » exclut la question. C'est la formule des dilemmes à deux options de la version 1, étendue à N options.</li>
        <li>Allocation : la part de points de chaque option, centrée sur la répartition uniforme, multiplie ses poids ; une répartition égale est neutre.</li>
        <li>Chargements croisés : un item peut charger 2 ou 3 axes (poids secondaires 0,2 à 0,5), ce qui capture la logique d'intersection.</li>
        <li>Confiance : intervalle à 95 % par bootstrap sur les items ({BOOTSTRAP_DRAWS} tirages, calculés dans le navigateur). En dessous de {MIN_EFFECTIVE_ITEMS} items effectifs (n<sub>eff</sub> = (Σ|w|)² ⁄ Σw²), la position est dite « peu établie ».</li>
        <li>Cohérence : quand un même énoncé reçoit des réponses opposées dans deux contextes (gouvernement du camp opposé ou de votre camp), l'écart est signalé, avec une explication de la manière dont il peut se comprendre ; au plus trois signalements.</li>
        <li>Biais de réponse : un taux d'accord supérieur à 80 % ou inférieur à 20 % (acquiescence) ou un temps moyen inférieur à 1,5 s par question déclenchent un avertissement.</li>
      </ul>

      <h2>4. Carte, archétypes et indices</h2>
      <ul>
        <li>Carte 2D : abscisse = ECO ; ordonnée = indice « Ouverture–Fermeture » = {Object.entries(OPENNESS_WEIGHTS).map(([a, w]) => `${w} × ${a}`).join(' + ')} (poids renormalisés si un axe manque). Vue alternative : analyse en composantes principales ajustée sur les archétypes et les candidat·es codé·es sur au moins 8 axes.</li>
        <li>{data.archetypes.length} archétypes (courants de référence), dont les centroïdes sont justifiés par la littérature du fichier 02. Affinité = ½ × (1 + cosinus) ⁄ 2 + ½ × (1 − distance RMS ⁄ 200).</li>
        <li>Indices de convergence intersectionnelle (ALT, ECO, CUL), de fusionnisme (ECO libéral, CUL conservateur, REL traditionnel) et de souverainisme social (ECO socialiste, ETA et UE nationaux) : moyenne des composantes orientées, « marqué » si toutes dépassent +30.</li>
        <li>Textes de restitution : pour chaque axe et chaque niveau, une description neutre, des auteurs proches, la meilleure objection du pôle opposé et une question de réflexion ; {data.tensions.length} règles explicites de tension.</li>
      </ul>

      <h2>5. Correspondance avec les candidat·es</h2>
      <p>
        {data.candidates.length} candidatures sont recensées (déclarées, en primaire, pressenties ou incertaines), dont {coded} codées dans le fichier 01. Le codage −2..+2 est converti en −100..+100.
        Distance = racine de la moyenne pondérée des écarts au carré, sur les axes codés ; poids = confiance du codage (élevée {CONFIDENCE_WEIGHT.H}, moyenne {CONFIDENCE_WEIGHT.M}, faible {CONFIDENCE_WEIGHT.F})
        × saillance tirée de vos deux répartitions de priorités (bornée entre {SALIENCE_MIN} et {SALIENCE_MAX}). Les axes non codés sont ignorés ; une candidature n'est classée que si au moins {MIN_CODED_AXES} axes sont comparables.
        Aucune position n'est inventée : une donnée manquante est affichée « non renseigné ». Aucun·e candidat·e n'est qualifié·e moralement.
      </p>

      <h2>6. Validation</h2>
      <ul>
        <li>Neutralité : 10 000 répondants simulés aléatoirement obtiennent une moyenne comprise entre −5 et +5 sur chaque axe ; un répondant « tout d'accord » ne dépasse ±25 sur aucun axe.</li>
        <li>Personas : pour chaque candidat·e codé·e sur au moins 7 axes et chaque archétype, un répondant simulé selon son vecteur (plus un bruit aléatoire) le retrouve dans les trois plus proches dans au moins 90 % des cas.</li>
        <li>Validité interne : un script calcule l'alpha de Cronbach, l'oméga et une analyse factorielle sur des données pilotes importées manuellement ; aucune donnée n'est collectée automatiquement.</li>
        <li>Audit : la liste complète des items, chargements, explications et auteurs est publiée pour relecture par un panel pluraliste.</li>
      </ul>

      <h2>7. Limites</h2>
      <ul>
        <li>Les programmes 2027 sont incomplets : le codage des candidat·es est une hypothèse de calibrage, souvent de confiance moyenne ou faible, à faire auditer ; il repose parfois sur des programmes antérieurs.</li>
        <li>Aucun·e candidat·e n'est codé·e sur les axes secondaires ; quatre des cinq candidat·es de la primaire PS ne sont pas codé·es.</li>
        <li>Le questionnaire n'a pas encore été validé sur un échantillon pilote ; la rédaction des items et des textes, faite pour être équilibrée, doit être relue par des personnes de sensibilités différentes.</li>
        <li>Les archétypes sont des repères construits à partir de la littérature, pas des catégories statistiques.</li>
        <li>Réduire des convictions à quatorze nombres simplifie nécessairement : les textes et les objections comptent autant que les scores.</li>
      </ul>

      <h2>8. Sources</h2>
      <ul>
        <li>Fichier 01 : « Présidentielle 2027 — Programmes et mesures des candidats », état au {frDate(data.meta.dataDate)} (sources primaires ★★★, comparateur de la Fondation iFRAP ★★, agrégateurs ★ à revérifier).</li>
        <li>Fichier 02 : « Penseuses et penseurs des grands courants politiques, économiques et sociologiques » ({data.thinkers.length} fiches). Inclure un auteur ne vaut pas approbation.</li>
      </ul>
    </article>
  );
}
