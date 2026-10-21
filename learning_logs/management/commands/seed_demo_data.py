from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from learning_logs.models import Topic, Entry


class Command(BaseCommand):
    help = 'Seeds the database with demonstration users, topics, and learning entries for testing and evaluation.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding demo data..."))

        # Create or update superuser admin
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

        # Create or update demo student user
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

        # Topics & Entries definition
        sample_topics = [
            {
                'title': 'Python & Django Framework Mastery',
                'description': 'Core backend principles, Django ORM, class-based vs function-based views, authentication, and REST API development.',
                'entries': [
                    {
                        'title': 'Django Request-Response Flow & Architecture',
                        'content': (
                            "1. Incoming HTTP request hits WSGI/ASGI handler.\n"
                            "2. Security and session middlewares process the request sequentially.\n"
                            "3. URL Dispatcher matches the requested path in ROOT_URLCONF and extracts route arguments.\n"
                            "4. Target View function/class executes, performing database queries via Django ORM.\n"
                            "5. Template engine renders context data into HTML or JSON.\n"
                            "6. Response travels back through response middlewares and is sent to the client.\n\n"
                            "Key Takeaway: Middlewares provide centralized hooks for authentication, CSRF validation, and security headers."
                        )
                    },
                    {
                        'title': 'Optimizing ORM Queries: select_related vs prefetch_related',
                        'content': (
                            "Preventing N+1 queries in Django:\n"
                            "- select_related: Performs an SQL JOIN. Best suited for single-valued relationships (ForeignKey and OneToOneField).\n"
                            "- prefetch_related: Executes separate queries and performs in-memory joins in Python. Ideal for multi-valued relationships (ManyToManyField and reverse ForeignKey).\n\n"
                            "Example:\n"
                            "Entry.objects.select_related('topic').all()\n"
                            "Topic.objects.prefetch_related('entries').all()"
                        )
                    },
                    {
                        'title': 'Securing Django Web Applications',
                        'content': (
                            "Core security best practices implemented:\n"
                            "- CSRF tokens on all state-changing POST forms via {% csrf_token %}.\n"
                            "- Password hashing using PBKDF2 with SHA-256.\n"
                            "- Object-level authorization checks to isolate multi-tenant user data.\n"
                            "- Strict HTTP-only cookies and secure headers in production.\n"
                            "- Safe SQL queries via parameterized ORM methods."
                        )
                    }
                ]
            },
            {
                'title': 'Data Structures & Algorithms',
                'description': 'Foundational computer science topics, time-complexity analysis, tree traversals, and dynamic programming patterns.',
                'entries': [
                    {
                        'title': 'Big-O Notation & Complexity Trade-Offs',
                        'content': (
                            "Reviewing algorithm asymptotic bounds:\n"
                            "- O(1) Constant Time: Hash table lookup, array index access.\n"
                            "- O(log n) Logarithmic Time: Binary search on sorted arrays.\n"
                            "- O(n) Linear Time: Single pass array traversal.\n"
                            "- O(n log n) Linearithmic: Merge sort, Quick sort (average).\n"
                            "- O(n^2) Quadratic: Nested loops, bubble sort.\n\n"
                            "Rule of Thumb: When data scales beyond 100,000 records, strive for O(n log n) or better."
                        )
                    },
                    {
                        'title': 'Graph Traversal: BFS vs DFS',
                        'content': (
                            "Breadth-First Search (BFS):\n"
                            "- Uses a Queue (FIFO).\n"
                            "- Finds the shortest path in unweighted graphs.\n"
                            "- Explores node level by level.\n\n"
                            "Depth-First Search (DFS):\n"
                            "- Uses a Stack (LIFO) or recursion.\n"
                            "- Excellent for topological sorting, cycle detection, and maze solving."
                        )
                    }
                ]
            },
            {
                'title': 'System Design & Modern Web Architecture',
                'description': 'Scalability, microservices vs monoliths, caching layers, and database partitioning.',
                'entries': [
                    {
                        'title': 'Caching Strategies: Write-Through vs Cache-Aside',
                        'content': (
                            "In Cache-Aside (Lazy Loading):\n"
                            "1. Application looks for data in cache (Redis/Memcached).\n"
                            "2. On cache miss, it reads from primary database and populates cache.\n"
                            "3. Subsequent reads hit cache with sub-millisecond response.\n\n"
                            "Write-Through:\n"
                            "Application updates cache and database synchronously, ensuring immediate read consistency."
                        )
                    }
                ]
            }
        ]

        for topic_data in sample_topics:
            topic, _ = Topic.objects.get_or_create(
                user=demo_user,
                title=topic_data['title'],
                defaults={'description': topic_data['description']}
            )
            for entry_data in topic_data['entries']:
                Entry.objects.get_or_create(
                    topic=topic,
                    title=entry_data['title'],
                    defaults={'content': entry_data['content']}
                )

        self.stdout.write(self.style.SUCCESS("Successfully seeded demo data for 'student_demo'!"))
