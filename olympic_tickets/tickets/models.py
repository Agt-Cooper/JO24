# Create your models here.
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import secrets, qrcode
from io import BytesIO
from django.core.files.base import ContentFile

# Les offres
class Offer(models.Model):
    SOLO = 'solo'
    DUO = 'duo'
    FAMILLE = 'famille'

    OFFER_TYPES = [
        (SOLO, 'Solo (1 personne)'),
        (DUO, 'Duo (2 personnes)'),
        (FAMILLE, 'Famille (4 personnes)'),
    ]

    name = models.CharField(max_length=100)
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPES)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f'{self.name} - {self.get_offer_type_display()}'

    class Meta:
        unique_together = ('name', 'offer_type') #pour empcher les doublons

# Profile : clé 1
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    signup_key = models.CharField(max_length=64, unique=True, editable=False) # CLE 1 au signup #ajout ancien editable=False, unique=True)

    def save(self, *args, **kwargs):
        if not self.signup_key:
            self.signup_key = secrets.token_urlsafe(32)
        return super().save(*args, **kwargs)
    # ajout
    def __str__(self):
        return f'Profile({self.user.username})'

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
    # fin ajout

# Les commandes
class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default="pending")  # pending/paid/cancelled
    purchase_key = models.CharField(max_length=64, editable=False, blank=True)  # clé2
    #ajout ligne suivante
    def __str__(self):
        return f'Order #{self.id} - {self.user} - {self.status}'

class OrderItem(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="items")
    offer = models.ForeignKey("Offer", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Ajouts pour e-billet :
    purchase_key = models.CharField(max_length=100, blank=True, null=True)
    final_ticket_key = models.CharField(max_length=255, blank=True, null=True)
    qr_code = models.ImageField(upload_to="tickets_qr/", blank=True, null=True)

    def generate_ticket(self, user_key):
        import secrets
        self.purchase_key = secrets.token_urlsafe(32)
        self.final_ticket_key = f"{user_key}{self.purchase_key}"

        # Génération du QR code
        img = qrcode.make(self.final_ticket_key)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        self.qr_code.save(f"ticket_{self.pk}.png", ContentFile(buffer.getvalue()), save=False)
        buffer.close()
        self.save()

class Ticket(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    final_key = models.CharField(max_length=200, editable=False)  # concat clé1+clé2 (et éventuellement un sel)
    qrcode_image = models.ImageField(upload_to="qrcodes/", blank=True, null=True)  # nécessite MEDIA_*
    #ajout Ligne suivante
    def __str__(self):
        return f'Ticket for order #{self.order_id}'


