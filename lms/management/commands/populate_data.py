# lms/management/commands/populate_data.py
from django.core.management.base import BaseCommand
from django.db import transaction
from lms.models import (
    EducationLevel, Grade, SubjectCategory, Subject, 
    ResourceType, Resource
)
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Populate the database with initial CBC curriculum data'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Starting to populate data...')
        
        # Create Resource Types
        resource_types = [
            ResourceType(name='PDF', icon='fas fa-file-pdf', description='Portable Document Format files'),
            ResourceType(name='Video', icon='fas fa-video', description='Video files'),
            ResourceType(name='Audio', icon='fas fa-file-audio', description='Audio files'),
            ResourceType(name='Document', icon='fas fa-file-word', description='Word documents'),
            ResourceType(name='Presentation', icon='fas fa-file-powerpoint', description='PowerPoint presentations'),
            ResourceType(name='Spreadsheet', icon='fas fa-file-excel', description='Excel spreadsheets'),
            ResourceType(name='Image', icon='fas fa-image', description='Image files'),
        ]
        
        for rt in resource_types:
            rt_obj, created = ResourceType.objects.get_or_create(
                name=rt.name,
                defaults={'icon': rt.icon, 'description': rt.description}
            )
            if created:
                self.stdout.write(f'Created resource type: {rt.name}')
        
        # Create Subject Categories - Include all categories from the curriculum
        categories_data = [
            {'name': 'Languages', 'icon': 'fas fa-language', 'description': 'Language and communication subjects'},
            {'name': 'Mathematics', 'icon': 'fas fa-calculator', 'description': 'Mathematics and numerical subjects'},
            {'name': 'Science', 'icon': 'fas fa-flask', 'description': 'Science and experimental subjects'},
            {'name': 'Humanities', 'icon': 'fas fa-book', 'description': 'Social sciences and humanities'},
            {'name': 'Technical', 'icon': 'fas fa-cogs', 'description': 'Technical and vocational subjects'},
            {'name': 'Arts', 'icon': 'fas fa-palette', 'description': 'Creative and performing arts'},
            {'name': 'Religious Studies', 'icon': 'fas fa-pray', 'description': 'Religious education subjects'},
            {'name': 'Physical Education', 'icon': 'fas fa-running', 'description': 'Physical health and sports subjects'},
            {'name': 'Life Skills', 'icon': 'fas fa-hands-helping', 'description': 'Life skills and personal development'},
            {'name': 'Home Science', 'icon': 'fas fa-home', 'description': 'Home science and domestic education subjects'},
        ]
        
        category_objects = {}
        for cat_data in categories_data:
            cat_obj, created = SubjectCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'description': cat_data['description']
                }
            )
            category_objects[cat_data['name']] = cat_obj
            if created:
                self.stdout.write(f'Created subject category: {cat_data["name"]}')
        
        # Create Education Levels and their Grades
        education_levels_data = [
            {
                'name': 'Pre-Primary',
                'icon': 'fas fa-child',
                'order': 1,
                'description': 'Early childhood education for young learners',
                'grades': ['PG', 'PP1', 'PP2'],
                'subjects': {
                    'Religious Studies': ['CRE', 'IRE', 'HRE'],
                    'Mathematics': ['Mathematics'],
                    'Languages': ['Languages'],
                    'Humanities': ['Environment'],
                    'Arts': ['Psychomotor']
                }
            },
            {
                'name': 'Lower Primary',
                'icon': 'fas fa-school',
                'order': 2,
                'description': 'Foundational education for early primary learners',
                'grades': ['G1', 'G2', 'G3'],
                'subjects': {
                    'Arts': ['Creative Activities'],
                    'Languages': ['English Activities', 'Kiswahili'],
                    'Religious Studies': ['HRE', 'IRE'],
                    'Mathematics': ['Mathematics']
                }
            },
            {
                'name': 'Upper Primary',
                'icon': 'fas fa-graduation-cap',
                'order': 3,
                'description': 'Intermediate education for upper primary learners',
                'grades': ['G4', 'G5', 'G6'],
                'subjects': {
                    'Mathematics': ['Mathematics'],
                    'Languages': ['Kiswahili'],
                    'Home Science': ['Home Science'],
                    'Humanities': ['Social Studies'],
                    'Arts': ['Music'],
                    'Physical Education': ['PE'],
                    'Languages': ['Chinese', 'German', 'Indigenous Language'],
                    'Physical Education': ['PHE']
                }
            },
            {
                'name': 'Junior Secondary',
                'icon': 'fas fa-users',
                'order': 4,
                'description': 'Middle school education for secondary learners',
                'grades': ['G7', 'G8', 'G9'],
                'subjects': {
                    'Mathematics': ['Mathematics'],
                    'Languages': ['Kiswahili', 'English'],
                    'Science': ['Biology'],
                    'Languages': ['Arabic', 'French', 'German'],
                    'Technical': ['Pre-Technical'],
                    'Life Skills': ['Life Skills'],
                    'Science': ['Computer Science', 'Integrated Science'],
                    'Physical Education': ['Physical Health Education', 'Sports']
                }
            },
            {
                'name': 'Senior Secondary',
                'icon': 'fas fa-user-graduate',
                'order': 5,
                'description': 'Advanced education for senior secondary learners',
                'grades': ['G10', 'G11', 'G12'],
                'subjects': {
                    'Science': ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science'],
                    'Technical': ['Technical Subjects'],
                    'Humanities': ['Geography', 'History and Government', 'Religious Education', 'Business Education'],
                    'Languages': ['Kiswahili', 'English'],
                    'Arts': ['Music', 'Drama', 'Dance', 'Visual Arts', 'Home Science', 'Fashion Design']
                }
            }
        ]
        
        # Create Education Levels and Grades
        level_objects = {}
        grade_objects = {}
        
        for level_data in education_levels_data:
            # Create Education Level
            level_obj, created = EducationLevel.objects.get_or_create(
                name=level_data['name'],
                defaults={
                    'icon': level_data['icon'],
                    'order': level_data['order'],
                    'description': level_data['description']
                }
            )
            level_objects[level_data['name']] = level_obj
            if created:
                self.stdout.write(f'Created education level: {level_data["name"]}')
            
            # Create Grades for this level
            for i, grade_name in enumerate(level_data['grades']):
                grade_obj, created = Grade.objects.get_or_create(
                    name=grade_name,
                    education_level=level_obj,
                    defaults={
                        'order': i + 1,
                        'description': f'{grade_name} in {level_data["name"]} education'
                    }
                )
                grade_key = f"{level_data['name']}_{grade_name}"
                grade_objects[grade_key] = grade_obj
                if created:
                    self.stdout.write(f'  Created grade: {grade_name}')
        
        # Create Subjects and assign to Grades
        subject_objects = {}
        
        for level_data in education_levels_data:
            level_obj = level_objects[level_data['name']]
            
            # Process subjects by category
            processed_subjects = {}
            for category_name, subject_names in level_data['subjects'].items():
                if category_name not in processed_subjects:
                    processed_subjects[category_name] = []
                processed_subjects[category_name].extend(subject_names)
            
            # Create subjects for each category
            for category_name, subject_names in processed_subjects.items():
                if category_name not in category_objects:
                    self.stdout.write(
                        self.style.WARNING(f'Category {category_name} not found, skipping subjects')
                    )
                    continue
                    
                category_obj = category_objects[category_name]
                
                for subject_name in subject_names:
                    # Create Subject
                    subject_obj, created = Subject.objects.get_or_create(
                        name=subject_name,
                        category=category_obj,
                        defaults={'description': f'{subject_name} subject for {level_data["name"]}'}
                    )
                    
                    if created:
                        self.stdout.write(f'  Created subject: {subject_name} ({category_name})')
                    
                    subject_objects[subject_name] = subject_obj
                    
                    # Assign subject to all grades in this education level
                    for grade_name in level_data['grades']:
                        grade_key = f"{level_data['name']}_{grade_name}"
                        if grade_key in grade_objects:
                            grade_obj = grade_objects[grade_key]
                            if not subject_obj.grades.filter(id=grade_obj.id).exists():
                                subject_obj.grades.add(grade_obj)
                                self.stdout.write(f'    Assigned {subject_name} to {grade_name}')
        
        # Create Pathways for Senior Secondary
        senior_secondary = level_objects['Senior Secondary']
        
        pathways_data = [
            {
                'name': 'STEM',
                'subjects': ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science', 'Technical Subjects'],
                'description': 'Science, Technology, Engineering, and Mathematics pathway'
            },
            {
                'name': 'Social Sciences',
                'subjects': ['Geography', 'History and Government', 'Religious Education', 'Business Education', 'Kiswahili', 'English'],
                'description': 'Social sciences and humanities pathway'
            },
            {
                'name': 'Creative Arts and Sports',
                'subjects': ['Music', 'Drama', 'Dance', 'Visual Arts', 'Home Science', 'Fashion Design'],
                'description': 'Creative arts and sports pathway'
            }
        ]
        
        for pathway_data in pathways_data:
            for i in range(10, 13):  # G10, G11, G12
                grade_name = f'G{i}'
                grade_key = f"Senior Secondary_{grade_name}"
                
                if grade_key in grade_objects:
                    grade_obj = grade_objects[grade_key]
                    
                    # Create or get pathway
                    try:
                        from lms.models import Pathway
                        pathway_obj, created = Pathway.objects.get_or_create(
                            name=pathway_data['name'],
                            grade=grade_obj,
                            defaults={'description': pathway_data['description']}
                        )
                        
                        if created:
                            self.stdout.write(f'Created pathway: {pathway_data["name"]} for {grade_name}')
                        
                        # Assign subjects to pathway
                        for subject_name in pathway_data['subjects']:
                            if subject_name in subject_objects:
                                subject_obj = subject_objects[subject_name]
                                if not pathway_obj.subjects.filter(id=subject_obj.id).exists():
                                    pathway_obj.subjects.add(subject_obj)
                                    self.stdout.write(f'  Added {subject_name} to {pathway_data["name"]} pathway')
                    except ImportError:
                        self.stdout.write(
                            self.style.WARNING('Pathway model not available')
                        )
        
        # Create some sample resources
        try:
            pdf_type = ResourceType.objects.get(name='PDF')
            video_type = ResourceType.objects.get(name='Video')
            
            # Get a sample subject and grade
            math_subject = Subject.objects.filter(name='Mathematics').first()
            g7_grade = Grade.objects.filter(name='G7').first()
            
            if math_subject and g7_grade:
                # Use first superuser or create one
                try:
                    user = User.objects.filter(is_superuser=True).first()
                    if not user:
                        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
                except:
                    user = User.objects.create_user('admin', 'admin@example.com', 'admin')
                
                # Create sample resources
                sample_resources = [
                    {
                        'title': 'Introduction to Algebra',
                        'subject': math_subject,
                        'resource_type': pdf_type,
                        'description': 'Basic concepts of algebra for Grade 7 students',
                        'allow_download': True,
                        'is_premium': False
                    },
                    {
                        'title': 'Solving Linear Equations',
                        'subject': math_subject,
                        'resource_type': video_type,
                        'description': 'Video tutorial on solving linear equations',
                        'allow_download': True,
                        'is_premium': False
                    }
                ]
                
                for resource_data in sample_resources:
                    resource, created = Resource.objects.get_or_create(
                        title=resource_data['title'],
                        subject=resource_data['subject'],
                        defaults={
                            'resource_type': resource_data['resource_type'],
                            'uploaded_by': user,
                            'description': resource_data['description'],
                            'allow_download': resource_data['allow_download'],
                            'is_premium': resource_data['is_premium'],
                            'is_active': True
                        }
                    )
                    if created:
                        self.stdout.write(f'Created resource: {resource.title}')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not create sample resources: {str(e)}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated the database with CBC curriculum data')
        )