import requests
import concurrent.futures
from django.core.management.base import BaseCommand
from core.models import Category, Course, Lesson
import time

CATEGORIES = {
    "Development": {
        "icon": "bi-code-slash", "color": "#e0caff",
        "topics": [
            "Python (programming language)", "C (programming language)", "C++", "Java (programming language)", "JavaScript",
            "HTML", "CSS", "SQL", "NoSQL", "React (JavaScript library)", "Angular (web framework)", "Vue.js", "Django (web framework)",
            "Flask (web framework)", "Node.js", "Express.js", "Ruby on Rails", "Spring Framework", "ASP.NET", "Ruby (programming language)",
            "Go (programming language)", "Rust (programming language)", "Kotlin (programming language)", "Swift (programming language)",
            "TypeScript", "PHP", "Perl", "Objective-C", "Assembly language", "Mobile app development", "Web development",
            "Software engineering", "DevOps", "Docker (software)", "Kubernetes", "Git", "GitHub", "Version control",
            "Continuous integration", "Game development", "Unity (game engine)", "Unreal Engine", "Software testing", "Unit testing",
            "Test-driven development", "Agile software development", "Scrum (software development)", "Software architecture",
            "Microservices", "REST", "GraphQL", "WebAssembly", "Cloud computing", "Amazon Web Services", "Microsoft Azure", "Google Cloud",
            "Serverless computing", "Linux", "Bash (Unix shell)", "PowerShell", "Computer programming", "Object-oriented programming",
            "Functional programming", "Data structure", "Algorithm", "Computer network", "Network security", "Cryptography",
            "Operating system", "Database management system", "Relational database", "MongoDB", "PostgreSQL", "MySQL", "Redis",
            "Elasticsearch", "Apache Kafka", "RabbitMQ", "Apache Hadoop", "Apache Spark", "Flutter (software)", "React Native",
            "Xamarin", "Ionic (mobile app framework)", "Electron (software framework)", "Vim (text editor)", "Emacs"
        ][:85]
    },
    "AI & Data": {
        "icon": "bi-robot", "color": "#ffeaa7",
        "topics": [
            "Artificial intelligence", "Machine learning", "Deep learning", "Data science", "Big data", "Data mining",
            "Natural language processing", "Computer vision", "Reinforcement learning", "Neural network", "Artificial neural network",
            "Convolutional neural network", "Recurrent neural network", "Generative adversarial network", "Transformer (machine learning model)",
            "Large language model", "Data analytics", "Predictive analytics", "Statistical classification", "Regression analysis",
            "Cluster analysis", "Principal component analysis", "Support vector machine", "Random forest", "Decision tree learning",
            "Data visualization", "Business intelligence", "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas (software)",
            "NumPy", "Matplotlib", "Apache Spark", "Apache Hadoop", "Tableau Software", "Power BI", "Data warehouse", "Data lake",
            "Data engineering", "Feature engineering", "Dimensionality reduction", "Ensemble learning", "Q-learning", "Markov decision process",
            "Hidden Markov model", "Bayesian network", "Naive Bayes classifier", "K-nearest neighbors algorithm", "K-means clustering",
            "Hierarchical clustering", "Anomaly detection", "Time series", "Forecasting", "Speech recognition", "Image processing",
            "Robotics", "Expert system", "Knowledge representation and reasoning"
        ][:60]
    },
    "Business": {
        "icon": "bi-briefcase", "color": "#c3f0c8",
        "topics": [
            "Business", "Accounting", "Corporate finance", "Marketing", "Management", "Microeconomics", "Macroeconomics",
            "Entrepreneurship", "Human resources", "Supply chain management", "Operations management", "Strategic management",
            "Organizational behavior", "Business ethics", "Business law", "International business", "Financial accounting",
            "Management accounting", "Investment", "Risk management", "Social media marketing", "Digital marketing",
            "Content marketing", "Search engine optimization", "E-commerce", "Sales", "Business strategy", "Leadership",
            "Project management", "Time management", "Negotiation", "Public relations", "Customer relationship management",
            "Brand management", "Business administration", "Venture capital", "Private equity", "Financial technology",
            "Blockchain", "Smart contract", "Cryptocurrency", "Business intelligence", "Business analytics", "Data-driven business",
            "Design thinking"
        ][:45]
    }
}

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
    return f"Detailed content for {topic} is currently unavailable."

def get_subtopics(topic):
    try:
        # We search with context to get relevant results
        search_query = topic
        if '(' in topic:
             search_query = topic.split('(')[0].strip()
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': f"{search_query}",
            'utf8': 1,
            'format': 'json',
            'srlimit': 5
        }
        r = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            results = r.json().get('query', {}).get('search', [])
            titles = [res['title'] for res in results if res['title'].lower() != search_query.lower()]
            return titles[:3] if titles else [f"Introduction to {search_query}", f"Advanced {search_query}", f"Applications of {search_query}"]
    except:
        pass
    
    clean_topic = topic.split('(')[0].strip()
    return [f"Introduction to {clean_topic}", f"Advanced {clean_topic}", f"Applications of {clean_topic}"]

def process_course(topic, category_id, category_name):
    if Course.objects.filter(title__icontains=topic.split('(')[0].strip()).exists():
        return f"Course {topic} already exists. Skipping."
    
    course_desc = get_summary(topic)
    clean_title = topic.split('(')[0].strip()
    
    course = Course.objects.create(
        category_id=category_id,
        title=f"The Complete {clean_title} Masterclass",
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
            title=sub.split('(')[0].strip().title(),
            content=html_content,
            order=i+1
        )
    return f"Successfully created {category_name} course for {clean_title} with {len(subtopics)} lessons."

class Command(BaseCommand):
    help = 'Populates the database with courses for Development, AI & Data, and Business.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Initializing Categories...')
        
        all_tasks = []
        for cat_name, cat_data in CATEGORIES.items():
            category, _ = Category.objects.get_or_create(
                name=cat_name,
                defaults={"icon": cat_data["icon"], "color": cat_data["color"]}
            )
            for topic in cat_data["topics"]:
                all_tasks.append((topic, category.id, cat_name))

        self.stdout.write(f'Processing {len(all_tasks)} courses in parallel, this may take around 60 seconds...')
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = {executor.submit(process_course, t[0], t[1], t[2]): t for t in all_tasks}
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        self.stdout.write(self.style.SUCCESS(result))
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f'Topic generated an exception: {exc}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully populated {len(all_tasks)} courses across categories!'))
