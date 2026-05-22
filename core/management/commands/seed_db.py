from django.core.management.base import BaseCommand
from faker import Faker
from users.models import User
from properties.models import Property, Room, Amenity
from bookings.models import Booking
from reviews.models import Review, HostReview
from rest_framework.authtoken.models import Token
from django.utils import timezone
from datetime import timedelta
import random


fake = Faker('it_IT')  # dati in italiano


class Command(BaseCommand):
    # Messaggio che appare quando esegui python manage.py help seed_db
    help = 'Popola il database con dati di test usando Faker'

    def add_arguments(self, parser):
        # Argomenti opzionali — python manage.py seed_db --users 10
        parser.add_argument('--users', type=int, default=5, help='Numero di utenti da creare')
        parser.add_argument('--properties', type=int, default=3, help='Numero di properties per host')
        parser.add_argument('--rooms', type=int, default=3, help='Numero di stanze per property')
        parser.add_argument('--bookings', type=int, default=2, help='Numero di prenotazioni per stanza')

    def handle(self, *args, **options):
        self.stdout.write('🌱 Inizio seeding del database...')

        # Creiamo le amenities base
        amenities = self.create_amenities()
        self.stdout.write(self.style.SUCCESS(f'✅ Create {len(amenities)} amenities'))

        # Creiamo gli utenti
        users = self.create_users(options['users'])
        self.stdout.write(self.style.SUCCESS(f'✅ Creati {len(users)} utenti'))

        # Dividiamo gli utenti in host e guest
        hosts = users[:len(users)//2]  # prima metà sono host
        guests = users[len(users)//2:]  # seconda metà sono guest

        # Creiamo le properties e le stanze
        rooms = self.create_properties_and_rooms(hosts, amenities, options['properties'], options['rooms'])
        self.stdout.write(self.style.SUCCESS(f'✅ Create properties e {len(rooms)} stanze'))

        # Creiamo le prenotazioni
        bookings = self.create_bookings(guests, rooms, options['bookings'])
        self.stdout.write(self.style.SUCCESS(f'✅ Create {len(bookings)} prenotazioni'))

        # Creiamo le recensioni
        self.create_reviews(bookings)
        self.stdout.write(self.style.SUCCESS('✅ Create recensioni'))

        self.stdout.write(self.style.SUCCESS('🎉 Seeding completato!'))


    def create_amenities(self):
        amenity_list = [
            {'name': 'WiFi', 'icon_slug': 'wifi'},
            {'name': 'Parcheggio', 'icon_slug': 'parking'},
            {'name': 'Cucina', 'icon_slug': 'kitchen'},
            {'name': 'Lavatrice', 'icon_slug': 'washer'},
            {'name': 'Aria condizionata', 'icon_slug': 'ac'},
            {'name': 'TV', 'icon_slug': 'tv'},
            {'name': 'Piscina', 'icon_slug': 'pool'},
            {'name': 'Palestra', 'icon_slug': 'gym'},
        ]
        amenities = []
        for a in amenity_list:
            # get_or_create evita duplicati se eseguiamo il comando più volte
            amenity, created = Amenity.objects.get_or_create(
                name=a['name'],
                defaults={'icon_slug': a['icon_slug']}
            )
            amenities.append(amenity)
        return amenities


    def create_users(self, num_users):
        users = []
        for i in range(num_users):
            username = fake.user_name()[:15]  # max 15 caratteri
            email = fake.email()

            # Evitiamo duplicati di username e email
            if User.objects.filter(username=username).exists():
                username = f"{username[:10]}{random.randint(1,999)}"
            if User.objects.filter(email=email).exists():
                continue

            user = User.objects.create(
                username=username,
                email=email,
                is_active=True,  # attiviamo direttamente senza OTP
                role='guest'
            )
            user.set_password('Test1234!')
            user.save()

            # Creiamo il token per ogni utente
            Token.objects.get_or_create(user=user)
            users.append(user)

        return users


    def create_properties_and_rooms(self, hosts, amenities, num_properties, num_rooms):
        rooms = []
        room_types = ['entire_place', 'private_room', 'shared_room']

        for host in hosts:
            # Rendiamo l'utente host
            host.role = 'host'
            host.save(update_fields=['role'])

            for _ in range(num_properties):
                property = Property.objects.create(
                    host=host,
                    name=f"{fake.word().capitalize()} {random.choice(['House', 'Villa', 'Appartamento', 'Loft'])}",
                    description=fake.paragraph(nb_sentences=3),
                    address=fake.street_address(),
                    city=fake.city(),
                    country='Italia',
                    latitude=float(fake.latitude()),
                    longitude=float(fake.longitude()),
                )

                for _ in range(num_rooms):
                    room = Room.objects.create(
                        property=property,
                        name=fake.word().capitalize(),
                        description=fake.paragraph(nb_sentences=2),
                        price_per_night=random.randint(50, 300),
                        max_guests=random.randint(1, 8),
                        num_beds=random.randint(1, 4),
                        num_bathrooms=random.randint(1, 3),
                        room_type=random.choice(room_types),
                        is_available=True,
                    )
                    # Aggiungiamo amenities casuali alla stanza
                    random_amenities = random.sample(amenities, random.randint(2, 5))
                    room.amenities.set(random_amenities)
                    rooms.append(room)

        return rooms


    def create_bookings(self, guests, rooms, num_bookings):
        bookings = []

        for room in rooms:
            for _ in range(num_bookings):
                guest = random.choice(guests)

                # Generiamo date future casuali
                check_in = timezone.now().date() + timedelta(days=random.randint(1, 60))
                check_out = check_in + timedelta(days=random.randint(1, 14))

                # Controlliamo sovrapposizioni
                overlapping = Booking.objects.filter(
                    room=room,
                    status__in=['pending', 'confirmed'],
                    check_in__lt=check_out,
                    check_out__gt=check_in
                ).exists()

                if overlapping:
                    continue

                num_nights = (check_out - check_in).days
                total_price = room.price_per_night * num_nights

                booking = Booking.objects.create(
                    room=room,
                    guest=guest,
                    check_in=check_in,
                    check_out=check_out,
                    num_guests=random.randint(1, room.max_guests),
                    total_price=total_price,
                    # Alcune prenotazioni confirmed, alcune pending
                    status=random.choice(['pending', 'confirmed']),
                    notes=fake.sentence() if random.random() > 0.5 else None,
                )
                bookings.append(booking)

        return bookings


    def create_reviews(self, bookings):
        # Creiamo recensioni solo per prenotazioni confirmed
        confirmed_bookings = [b for b in bookings if b.status == 'confirmed']

        for booking in confirmed_bookings:
            # Recensione del guest sulla stanza
            if not Review.objects.filter(booking=booking).exists():
                Review.objects.create(
                    booking=booking,
                    author=booking.guest,
                    room=booking.room,
                    rating=random.randint(1, 5),
                    comment=fake.paragraph(nb_sentences=2),
                )

            # Recensione dell'host sul guest
            if not HostReview.objects.filter(booking=booking).exists():
                HostReview.objects.create(
                    booking=booking,
                    author=booking.room.property.host,
                    target_user=booking.guest,
                    rating=random.randint(1, 5),
                    comment=fake.paragraph(nb_sentences=2),
                )