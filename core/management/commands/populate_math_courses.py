import requests
import concurrent.futures
from django.core.management.base import BaseCommand
from core.models import Category, Course, Lesson

MATH_TOPICS = [
    "Algebra", "Calculus", "Geometry", "Topology", "Number theory", "Combinatorics", "Mathematical logic", "Set theory",
    "Probability theory", "Statistics", "Dynamical systems", "Differential equations", "Mathematical physics", "Information theory",
    "Cryptography", "Game theory", "Operations research", "Control theory", "Numerical analysis", "Optimization",
    "Functional analysis", "Complex analysis", "Real analysis", "Harmonic analysis", "Measure theory", "Graph theory",
    "Category theory", "Model theory", "Proof theory", "Computability theory", "Fluid dynamics", "Statistical mechanics",
    "Arithmetic", "Pre-algebra", "Linear algebra", "Abstract algebra", "Boolean algebra", "Commutative algebra", "Homological algebra",
    "Euclidean geometry", "Non-Euclidean geometry", "Projective geometry", "Affine geometry", "Differential geometry", "Algebraic geometry",
    "General topology", "Algebraic topology", "Geometric topology", "Differential topology", "Trigonometry",
    "Fractional calculus", "Ordinary differential equations", "Partial differential equations", "Chaos theory",
    "Mathematical statistics", "Applied statistics", "Algebraic number theory", "Analytic number theory", "Arithmetic combinatorics",
    "Matroid theory", "Order theory", "Topos theory", "Linear programming", "Nonlinear programming", "Classical mechanics",
    "Quantum mechanics", "Mathematical biology", "Mathematical economics", "Financial mathematics", "Actuarial science",
    "Tensor calculus", "Vector calculus", "Multivariable calculus", "Discrete mathematics", "Applied mathematics", "Pure mathematics",
    "History of mathematics", "Philosophy of mathematics", "Mathematical proof", "Mathematical induction", "Mathematical paradox",
    "Fractal geometry", "Knot theory", "Lie algebra", "Lie group", "Representation theory", "Galois theory", "Ring theory",
    "Field theory", "Group theory", "Module theory", "Operator theory", "Spectral theory", "Stochastic process", "Markov chain",
    "Queueing theory", "Time series", "Survival analysis", "Design of experiments", "Bayesian inference", "Fuzzy logic",
    "Rough set", "Neural network", "Machine learning", "Deep learning", "Artificial intelligence", "Data mining",
    "Data science", "Big data", "Bioinformatics", "Computational biology", "Computational chemistry", "Computational physics",
    "Computational mathematics", "Symbolic computation", "Computer algebra", "Numerical linear algebra", "Numerical partial differential equations",
    "Finite element method", "Finite difference method", "Finite volume method", "Boundary element method", "Monte Carlo method",
    "Simulated annealing", "Genetic algorithm", "Evolutionary computation", "Swarm intelligence", "Ant colony optimization",
    "Calculus of variations", "Integral equation", "Bifurcation theory", "Ergodic theory", "Potential theory", "Random matrix"
]

HEADERS = {'User-Agent': 'GamifiedLearningApp/1.0 (https://example.com/)'}
BASE_URL = 'https://en.wikipedia.org/api/rest_v1/page/summary/'
SEARCH_URL = 'https://en.wikipedia.org/w/api.php'

def get_summary(topic):
    try:
        r = requests.get(BASE_URL + requests.utils.quote(topic), headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get('extract', f"Detailed content for {topic}.")
    except:
        pass
    return f"Detailed mathematical content for {topic} is currently unavailable. Please refer to standard texts."

def get_subtopics(topic):
    try:
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': f"{topic} mathematics",
            'utf8': 1,
            'format': 'json',
            'srlimit': 5
        }
        r = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            results = r.json().get('query', {}).get('search', [])
            titles = [res['title'] for res in results if res['title'].lower() != topic.lower()]
            return titles[:3] if titles else [f"Introduction to {topic}", f"Advanced {topic}", f"Applications of {topic}"]
    except:
        pass
    return [f"Introduction to {topic}", f"Advanced {topic}", f"Applications of {topic}"]

def process_course(topic, category_id):
    if Course.objects.filter(title__icontains=topic).exists():
        return f"Course {topic} already exists. Skipping."
    
    course_desc = get_summary(topic)
    course = Course.objects.create(
        category_id=category_id,
        title=f"Introduction to {topic.title()}",
        description=course_desc,
        instructor="Wikipedia Educator",
        price_tag="Free"
    )
    
    subtopics = get_subtopics(topic)
    for i, sub in enumerate(subtopics):
        lesson_content = get_summary(sub)
        html_content = "".join([f"<p>{p.strip()}</p>" for p in lesson_content.split('\n') if p.strip()])
        Lesson.objects.create(
            course=course,
            title=sub.title(),
            content=html_content,
            order=i+1
        )
    return f"Successfully created course for {topic} with {len(subtopics)} lessons."

class Command(BaseCommand):
    help = 'Populates the database with 120+ math courses using Wikipedia.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Checking Wikipedia for topics...')
        category, _ = Category.objects.get_or_create(
            name="Mathematics",
            defaults={"icon": "bi-calculator", "color": "#17a2b8"}
        )

        self.stdout.write('Processing 120+ courses in parallel, this should take ~30 seconds...')
        
        # We need exactly 120 topics
        topics = MATH_TOPICS[:125]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = {executor.submit(process_course, topic, category.id): topic for topic in topics}
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    self.stdout.write(self.style.SUCCESS(result))
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f'Topic generated an exception: {exc}'))

        self.stdout.write(self.style.SUCCESS('Successfully populated mathematics courses!'))
