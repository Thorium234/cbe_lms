# lms/management/commands/import_pdfs.py
import os
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from lms.models import (
    EducationLevel, Grade, Subject, ResourceType, 
    Resource, SubjectCategory
)
from django.core.files import File
from pathlib import Path

class Command(BaseCommand):
    help = 'Import PDFs from directory and organize them into grades and subjects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pdf-dir',
            type=str,
            default='/home/thorium/Documents/pdfs_docs',
            help='Directory containing PDF files to import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        pdf_directory = options['pdf_dir']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Get the default user for uploads (first superuser)
        User = get_user_model()
        try:
            uploader = User.objects.filter(is_superuser=True).first()
            if not uploader:
                uploader = User.objects.first()
        except:
            self.stdout.write(
                self.style.ERROR('No users found in the system')
            )
            return
        
        self.stdout.write(f'Using {uploader.username} as uploader')
        
        # Get or create PDF resource type
        pdf_type, created = ResourceType.objects.get_or_create(
            name='PDF',
            defaults={
                'icon': 'fas fa-file-pdf',
                'description': 'Portable Document Format files'
            }
        )
        if created:
            self.stdout.write('Created PDF resource type')
        
        # Define mapping of file patterns to subjects and grades
        subject_mappings = {
            # Pre-Primary
            r'.*cre.*|.*religious.*|.*faith.*': {'subject': 'CRE', 'grade_pattern': r'.*pg.*|.*pp1.*|.*pp2.*', 'education_level': 'Pre-Primary'},
            r'.*ire.*|.*islamic.*|.*muslim.*': {'subject': 'IRE', 'grade_pattern': r'.*pg.*|.*pp1.*|.*pp2.*', 'education_level': 'Pre-Primary'},
            r'.*hre.*|.*hindu.*': {'subject': 'HRE', 'grade_pattern': r'.*pg.*|.*pp1.*|.*pp2.*', 'education_level': 'Pre-Primary'},
            r'.*math.*|.*mathematics.*|.*numbers.*': {'subject': 'Mathematics', 'grade_pattern': r'.*pg.*|.*pp1.*|.*pp2.*', 'education_level': 'Pre-Primary'},
            r'.*language.*|.*english.*|.*kiswahili.*': {'subject': 'Languages', 'grade_pattern': r'.*pg.*|.*pp1.*|.*pp2.*', 'education_level': 'Pre-Primary'},
            r'.*environment.*|.*science.*|.*nature.*': {'subject': 'Environment', 'grade_pattern': r'.*pg.*|.*pp1.*|.*pp2.*', 'education_level': 'Pre-Primary'},
            r'.*psychomotor.*|.*art.*|.*creative.*': {'subject': 'Psychomotor', 'grade_pattern': r'.*pg.*|.*pp1.*|.*pp2.*', 'education_level': 'Pre-Primary'},
            
            # Lower Primary
            r'.*creative.*|.*art.*|.*craft.*': {'subject': 'Creative Activities', 'grade_pattern': r'.*g1.*|.*g2.*|.*g3.*', 'education_level': 'Lower Primary'},
            r'.*english.*|.*activities.*': {'subject': 'English Activities', 'grade_pattern': r'.*g1.*|.*g2.*|.*g3.*', 'education_level': 'Lower Primary'},
            r'.*kiswahili.*': {'subject': 'Kiswahili', 'grade_pattern': r'.*g1.*|.*g2.*|.*g3.*', 'education_level': 'Lower Primary'},
            r'.*math.*|.*mathematics.*': {'subject': 'Mathematics', 'grade_pattern': r'.*g1.*|.*g2.*|.*g3.*', 'education_level': 'Lower Primary'},
            
            # Upper Primary
            r'.*math.*|.*mathematics.*': {'subject': 'Mathematics', 'grade_pattern': r'.*g4.*|.*g5.*|.*g6.*', 'education_level': 'Upper Primary'},
            r'.*kiswahili.*': {'subject': 'Kiswahili', 'grade_pattern': r'.*g4.*|.*g5.*|.*g6.*', 'education_level': 'Upper Primary'},
            r'.*home.*science.*': {'subject': 'Home Science', 'grade_pattern': r'.*g4.*|.*g5.*|.*g6.*', 'education_level': 'Upper Primary'},
            r'.*social.*studies.*': {'subject': 'Social Studies', 'grade_pattern': r'.*g4.*|.*g5.*|.*g6.*', 'education_level': 'Upper Primary'},
            r'.*music.*': {'subject': 'Music', 'grade_pattern': r'.*g4.*|.*g5.*|.*g6.*', 'education_level': 'Upper Primary'},
            r'.*pe.*|.*physical.*education.*': {'subject': 'PE', 'grade_pattern': r'.*g4.*|.*g5.*|.*g6.*', 'education_level': 'Upper Primary'},
            r'.*chinese.*': {'subject': 'Chinese', 'grade_pattern': r'.*g4.*|.*g5.*|.*g6.*', 'education_level': 'Upper Primary'},
            r'.*german.*': {'subject': 'German', 'grade_pattern': r'.*g4.*|.*g5.*|.*g6.*', 'education_level': 'Upper Primary'},
            r'.*indigenous.*language.*': {'subject': 'Indigenous Language', 'grade_pattern': r'.*g4.*|.*g5.*|.*g6.*', 'education_level': 'Upper Primary'},
            r'.*phe.*|.*physical.*health.*': {'subject': 'PHE', 'grade_pattern': r'.*g4.*|.*g5.*|.*g6.*', 'education_level': 'Upper Primary'},
            
            # Junior Secondary
            r'.*math.*|.*mathematics.*': {'subject': 'Mathematics', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*kiswahili.*': {'subject': 'Kiswahili', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*biology.*': {'subject': 'Biology', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*arabic.*': {'subject': 'Arabic', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*french.*': {'subject': 'French', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*german.*': {'subject': 'German', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*pre.*technical.*': {'subject': 'Pre-Technical', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*life.*skills.*': {'subject': 'Life Skills', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*computer.*science.*': {'subject': 'Computer Science', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*integrated.*science.*': {'subject': 'Integrated Science', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*physical.*health.*education.*': {'subject': 'Physical Health Education', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            r'.*sports.*': {'subject': 'Sports', 'grade_pattern': r'.*g7.*|.*g8.*|.*g9.*', 'education_level': 'Junior Secondary'},
            
            # Senior Secondary STEM
            r'.*math.*|.*mathematics.*': {'subject': 'Mathematics', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*physics.*': {'subject': 'Physics', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*chemistry.*': {'subject': 'Chemistry', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*biology.*': {'subject': 'Biology', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*computer.*science.*': {'subject': 'Computer Science', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*technical.*subjects.*': {'subject': 'Technical Subjects', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            
            # Senior Secondary Social Sciences
            r'.*geography.*': {'subject': 'Geography', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*history.*|.*government.*': {'subject': 'History and Government', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*religious.*|.*education.*': {'subject': 'Religious Education', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*business.*|.*education.*': {'subject': 'Business Education', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            
            # Senior Secondary Creative Arts
            r'.*music.*': {'subject': 'Music', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*drama.*': {'subject': 'Drama', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*dance.*': {'subject': 'Dance', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*visual.*arts.*': {'subject': 'Visual Arts', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
            r'.*fashion.*|.*design.*': {'subject': 'Fashion Design', 'grade_pattern': r'.*g10.*|.*g11.*|.*g12.*', 'education_level': 'Senior Secondary'},
        }
        
        # Create any missing subjects
        self.create_missing_subjects(subject_mappings)
        
        # Process PDF files
        pdf_path = Path(pdf_directory)
        if not pdf_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Directory {pdf_directory} does not exist')
            )
            return
        
        pdf_files = list(pdf_path.glob('*.pdf'))
        if not pdf_files:
            self.stdout.write(
                self.style.WARNING(f'No PDF files found in {pdf_directory}')
            )
            return
        
        self.stdout.write(f'Found {len(pdf_files)} PDF files to process')
        
        imported_count = 0
        skipped_count = 0
        
        for pdf_file in pdf_files:
            try:
                # Extract information from filename
                filename = pdf_file.stem.lower()
                file_size = pdf_file.stat().st_size
                
                # Find matching subject and grade
                matched = False
                for pattern, mapping in subject_mappings.items():
                    if re.search(pattern, filename, re.IGNORECASE):
                        # Find the education level
                        try:
                            education_level = EducationLevel.objects.get(
                                name=mapping['education_level']
                            )
                            
                            # Find matching grade based on pattern
                            grade = None
                            for grade_obj in education_level.grades.all():
                                if re.search(mapping['grade_pattern'], grade_obj.name.lower()):
                                    grade = grade_obj
                                    break
                            
                            if not grade:
                                # If no specific grade pattern matches, use first grade
                                grade = education_level.grades.first()
                            
                            if grade:
                                # Find the subject - use get_or_create to handle duplicates
                                category_name = self.get_category_for_subject(mapping['subject'])
                                category, _ = SubjectCategory.objects.get_or_create(
                                    name=category_name
                                )
                                
                                # Use get_or_create to handle duplicate subjects
                                subject, created = Subject.objects.get_or_create(
                                    name=mapping['subject'],
                                    category=category,
                                    defaults={'description': f'{mapping["subject"]} resources'}
                                )
                                
                                # Ensure the subject is linked to the grade
                                if grade not in subject.grades.all():
                                    subject.grades.add(grade)
                                    if created:
                                        self.stdout.write(
                                            f'Created subject: {mapping["subject"]} and linked to {grade.name}'
                                        )
                                    else:
                                        self.stdout.write(
                                            f'Linked existing subject: {mapping["subject"]} to {grade.name}'
                                        )
                                
                                # Create resource title from filename
                                title = self.generate_title_from_filename(filename)
                                
                                # Check if resource already exists
                                if Resource.objects.filter(
                                    title=title, 
                                    subject=subject
                                ).exists():
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'Skipping {pdf_file.name} - already exists'
                                        )
                                    )
                                    skipped_count += 1
                                    matched = True
                                    break
                                
                                if not dry_run:
                                    # Create the resource
                                    resource = Resource.objects.create(
                                        title=title,
                                        subject=subject,
                                        resource_type=pdf_type,
                                        uploaded_by=uploader,
                                        allow_download=True,
                                        is_active=True,
                                        file_size=file_size,
                                        description=f'Imported from {pdf_file.name}'
                                    )
                                    
                                    # Save the file
                                    with open(pdf_file, 'rb') as f:
                                        resource.file.save(
                                            f'{subject.category.name.lower()}/{grade.name.lower()}/{pdf_file.name}',
                                            File(f),
                                            save=True
                                        )
                                    
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f'Imported {pdf_file.name} -> {title}'
                                        )
                                    )
                                
                                imported_count += 1
                                matched = True
                                break
                                
                        except EducationLevel.DoesNotExist:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Education level {mapping["education_level"]} not found'
                                )
                            )
                
                if not matched:
                    self.stdout.write(
                        self.style.WARNING(
                            f'No match found for {pdf_file.name} - using default'
                        )
                    )
                    
                    # Use a default subject if no pattern matches
                    default_subject = self.get_default_subject()
                    if default_subject:
                        title = self.generate_title_from_filename(filename)
                        
                        if not Resource.objects.filter(title=title, subject=default_subject).exists():
                            if not dry_run:
                                resource = Resource.objects.create(
                                    title=title,
                                    subject=default_subject,
                                    resource_type=pdf_type,
                                    uploaded_by=uploader,
                                    allow_download=True,
                                    is_active=True,
                                    file_size=file_size,
                                    description=f'Imported from {pdf_file.name}'
                                )
                                
                                with open(pdf_file, 'rb') as f:
                                    resource.file.save(
                                        f'default/{pdf_file.name}',
                                        File(f),
                                        save=True
                                    )
                                
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Imported {pdf_file.name} to default subject'
                                    )
                                )
                                imported_count += 1
                        else:
                            skipped_count += 1
                    else:
                        skipped_count += 1
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing {pdf_file.name}: {str(e)}'
                    )
                )
                skipped_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Import complete: {imported_count} imported, {skipped_count} skipped'
            )
        )
    
    def create_missing_subjects(self, subject_mappings):
        """Create any subjects that don't exist"""
        for pattern, mapping in subject_mappings.items():
            try:
                education_level = EducationLevel.objects.get(
                    name=mapping['education_level']
                )
                
                # Check if subject exists - use get_or_create to handle duplicates
                category_name = self.get_category_for_subject(mapping['subject'])
                category, _ = SubjectCategory.objects.get_or_create(
                    name=category_name
                )
                
                # Use get_or_create instead of get to handle duplicates
                subject, created = Subject.objects.get_or_create(
                    name=mapping['subject'],
                    category=category,
                    defaults={'description': f'{mapping["subject"]} resources'}
                )
                
                # Ensure subject is linked to all grades in the education level
                for grade in education_level.grades.all():
                    if grade not in subject.grades.all():
                        subject.grades.add(grade)
                
                if created:
                    self.stdout.write(
                        f'Created subject: {mapping["subject"]}'
                    )
                        
            except EducationLevel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'Education level {mapping["education_level"]} not found'
                    )
                )
    
    def get_category_for_subject(self, subject_name):
        """Determine the appropriate category for a subject"""
        subject_name = subject_name.lower()
        
        categories = {
            'Languages': ['english', 'kiswahili', 'chinese', 'german', 'french', 'arabic', 'indigenous', 'language'],
            'Mathematics': ['math', 'mathematics'],
            'Science': ['physics', 'chemistry', 'biology', 'integrated science', 'computer science'],
            'Humanities': ['geography', 'history', 'government', 'social studies', 'religion', 'religious', 'business', 'life skills'],
            'Technical': ['pre-technical', 'technical', 'home science', 'fashion design'],
            'Arts': ['music', 'drama', 'dance', 'visual arts', 'creative', 'art', 'craft', 'psychomotor'],
            'Physical Education': ['pe', 'physical', 'education', 'health', 'sports', 'phe'],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in subject_name:
                    return category
        
        return 'Other'
    
    def generate_title_from_filename(self, filename):
        """Generate a readable title from the filename"""
        # Remove file extension and common patterns
        title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        
        # Capitalize words
        title = ' '.join(word.capitalize() for word in title.split())
        
        # Remove any numbers at the beginning
        title = re.sub(r'^\d+\s*', '', title)
        
        # Ensure it's not empty
        if not title.strip():
            title = 'Untitled Document'
        
        return title.strip()
    
    def get_default_subject(self):
        """Get a default subject for files that don't match any pattern"""
        try:
            # Try to find a general subject
            subject, created = Subject.objects.get_or_create(
                name='General Resources',
                defaults={'description': 'General educational resources'}
            )
            return subject
        except:
            return None
