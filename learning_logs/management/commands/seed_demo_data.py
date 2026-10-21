from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from learning_logs.models import (
    Topic, Entry, Summary, Quiz, Question, Choice,
    QuizAttempt, ChatSession, ChatMessage
)
from learning_logs.ai_service import MockAIProvider


class Command(BaseCommand):
    help = 'Seeds the database with demonstration users, topics, learning entries, summaries, and quizzes for testing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding comprehensive demo portfolio data..."))

        # 1. Superuser Admin
        admin_user, created_admin = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('AdminPassword123!')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        if created_admin:
            self.stdout.write(self.style.SUCCESS("Created superuser: admin (password: AdminPassword123!)"))
        else:
            self.stdout.write("Superuser 'admin' updated.")

        # 2. Demo Student User (B.Tech AI & ML / Cybersecurity student)
        demo_user, created_demo = User.objects.get_or_create(
            username='student_demo',
            defaults={'email': 'demo@example.com'}
        )
        demo_user.set_password('DemoPassword123!')
        demo_user.save()
        if created_demo:
            self.stdout.write(self.style.SUCCESS("Created demo user: student_demo (password: DemoPassword123!)"))
        else:
            self.stdout.write("Demo user 'student_demo' updated.")

        # 3. Sample topics matching prompt (AI, ML, Cybersecurity, Networking, Web Dev)
        sample_topics = [
            {
                'title': 'Cybersecurity & Ethical Hacking',
                'description': 'Network defense, threat modeling, web vulnerabilities, penetration testing concepts, and mitigation strategies.',
                'entries': [
                    {
                        'title': 'Cross-Site Scripting (XSS) Defenses',
                        'content': (
                            "Cross-Site Scripting (XSS) occurs when an application includes untrusted data in a web page without proper validation or escaping.\n"
                            "There are three primary variants:\n"
                            "1. Stored XSS: Malicious script permanently stored in database or logs.\n"
                            "2. Reflected XSS: Non-persistent script delivered in the request URI or form payload.\n"
                            "3. DOM-based XSS: Vulnerability exists entirely in client-side JavaScript execution.\n\n"
                            "Defenses and Mitigation:\n"
                            "- Context-aware output encoding (HTML, JavaScript, CSS).\n"
                            "- Content Security Policy (CSP) headers restricting script execution sources.\n"
                            "- Setting HttpOnly flags on session cookies to mitigate session hijacking."
                        )
                    },
                    {
                        'title': 'SQL Injection (SQLi) & Parameterized Queries',
                        'content': (
                            "SQL Injection happens when untrusted user input is directly concatenated into SQL statements without escaping.\n"
                            "Attack vectors include authentication bypass (e.g. ' OR 1=1 --), data exfiltration via UNION SELECT, and database destruction.\n\n"
                            "Remediation:\n"
                            "- Always use parameterized queries or an Object-Relational Mapper (Django ORM).\n"
                            "- Apply the principle of least privilege to database users.\n"
                            "- Avoid raw SQL formatting with f-strings or string concatenation."
                        )
                    }
                ]
            },
            {
                'title': 'Computer Networking & Protocols',
                'description': 'OSI model, TCP/IP stack, transport layer protocols, socket programming, and routing mechanisms.',
                'entries': [
                    {
                        'title': 'TCP vs UDP: Reliability and Handshake Mechanics',
                        'content': (
                            "Transport Layer Protocols Comparison:\n"
                            "Transmission Control Protocol (TCP):\n"
                            "- Connection-oriented protocol using a Three-Way Handshake (SYN, SYN-ACK, ACK).\n"
                            "- Guarantees reliable in-order delivery via sequence numbers and ACKs.\n"
                            "- Implements flow control (sliding window) and congestion control algorithms (CUBIC, Reno).\n\n"
                            "User Datagram Protocol (UDP):\n"
                            "- Connectionless, lightweight datagram protocol with minimal header overhead (8 bytes vs 20-60 bytes).\n"
                            "- No delivery guarantees, retransmissions, or ordering.\n"
                            "- Ideal for latency-sensitive real-time applications such as video streaming, VoIP, and multiplayer gaming."
                        )
                    }
                ]
            },
            {
                'title': 'Artificial Intelligence & Machine Learning',
                'description': 'Supervised and unsupervised learning, gradient descent, neural networks, evaluation metrics, and LLM architectures.',
                'entries': [
                    {
                        'title': 'Bias-Variance Tradeoff & Regularization',
                        'content': (
                            "Understanding model generalization error:\n"
                            "- High Bias (Underfitting): Model is overly simplistic and fails to capture underlying patterns in training data.\n"
                            "- High Variance (Overfitting): Model fits training noise and performs poorly on unseen test data.\n\n"
                            "Regularization Techniques:\n"
                            "- L1 Regularization (Lasso): Adds absolute weights penalty; induces sparsity and feature selection.\n"
                            "- L2 Regularization (Ridge): Adds squared weights penalty; shrinks coefficients to prevent extreme parameter values.\n"
                            "- Dropout: Randomly deactivates neurons during neural network training iterations to prevent co-adaptation."
                        )
                    },
                    {
                        'title': 'Transformer Architecture & Self-Attention',
                        'content': (
                            "The Transformer architecture replaces sequential recurrent models with parallel self-attention mechanisms.\n"
                            "- Scaled Dot-Product Attention: Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V.\n"
                            "- Multi-Head Attention allows the model to jointly attend to information from different representation subspaces.\n"
                            "- Positional encodings preserve token order since self-attention is permutation-invariant."
                        )
                    }
                ]
            },
            {
                'title': 'Python & Django Full-Stack Development',
                'description': 'Django architecture, MVT pattern, ORM query optimization, session security, and RESTful service design.',
                'entries': [
                    {
                        'title': 'Django Request-Response Lifecycle & MTV',
                        'content': (
                            "Django follows the Model-Template-View (MTV) pattern:\n"
                            "- Model: Manages data schemas and database interactions via Django ORM.\n"
                            "- View: Contains business logic, querysets, and authorization checks.\n"
                            "- Template: HTML presentations with template tags and filters.\n\n"
                            "Middleware Pipeline:\n"
                            "Requests pass sequentially through SecurityMiddleware, SessionMiddleware, CommonMiddleware, CsrfViewMiddleware, and AuthenticationMiddleware before reaching views."
                        )
                    }
                ]
            }
        ]

        mock_provider = MockAIProvider()

        for topic_data in sample_topics:
            topic, _ = Topic.objects.get_or_create(
                user=demo_user,
                title=topic_data['title'],
                defaults={'description': topic_data['description']}
            )
            for entry_data in topic_data['entries']:
                entry, _ = Entry.objects.get_or_create(
                    topic=topic,
                    title=entry_data['title'],
                    defaults={'content': entry_data['content']}
                )

                # Seed an AI Summary for first entry of each topic
                if not Summary.objects.filter(entry=entry).exists():
                    ai_sum = mock_provider.summarize(entry.title, entry.content)
                    Summary.objects.create(
                        entry=entry,
                        user=demo_user,
                        summary_text=ai_sum['summary'],
                        key_points="\n".join(ai_sum['key_points']),
                        key_terms="\n".join(ai_sum['key_terms']),
                        is_mock=True
                    )

        # 4. Seed a sample Quiz and Attempt for Networking entry
        networking_entry = Entry.objects.filter(topic__user=demo_user, title__icontains='TCP vs UDP').first()
        if networking_entry and not Quiz.objects.filter(entry=networking_entry).exists():
            quiz = Quiz.objects.create(
                entry=networking_entry,
                user=demo_user,
                title="Quiz: TCP vs UDP Networking Protocols",
                is_mock=True
            )
            raw_questions = mock_provider.generate_quiz(networking_entry.title, networking_entry.content, num_questions=3)
            for q_idx, q_data in enumerate(raw_questions, start=1):
                question = Question.objects.create(
                    quiz=quiz,
                    text=q_data['question'],
                    explanation=q_data['explanation'],
                    order=q_idx
                )
                for c_idx, c_data in enumerate(q_data['choices'], start=1):
                    Choice.objects.create(
                        question=question,
                        text=c_data['text'],
                        is_correct=c_data['is_correct'],
                        order=c_idx
                    )

            # Record a sample attempt
            QuizAttempt.objects.create(
                quiz=quiz,
                user=demo_user,
                score=3,
                total_questions=3,
                percentage=100.0
            )

        # 5. Seed a sample Chat Session in Ask My Notes
        if not ChatSession.objects.filter(user=demo_user).exists():
            chat = ChatSession.objects.create(
                user=demo_user,
                title="Explaining TCP and XSS Concepts"
            )
            ChatMessage.objects.create(
                session=chat,
                role='user',
                content='What are the key differences between TCP and UDP in my notes?'
            )
            ChatMessage.objects.create(
                session=chat,
                role='assistant',
                content=(
                    "[DEMO AI ASSISTANT - Answering from 'TCP vs UDP: Reliability and Handshake Mechanics']\n\n"
                    "Based on your notes:\n"
                    "- **TCP** is connection-oriented, performs a 3-way handshake, and guarantees reliable, ordered packet delivery with congestion control.\n"
                    "- **UDP** is connectionless with smaller header overhead (8 bytes), provides no delivery guarantees, and is prioritized for latency-sensitive streaming and real-time communications.\n\n"
                    "💡 *Source Reference:* Retrieved directly from your note titled **TCP vs UDP: Reliability and Handshake Mechanics**."
                ),
                retrieved_notes="TCP vs UDP: Reliability and Handshake Mechanics"
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded comprehensive demo portfolio data!"))
