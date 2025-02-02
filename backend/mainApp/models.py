from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sessions.models import Session
from django.db import models

from PIL import Image


def createThumbnail(imagePath):
    img = Image.open(imagePath)
    img.thumbnail(settings.IMG_THUMBNAIL_SIZE)
    chunks = imagePath.split(".")
    chunks[-2] += "_"+("x".join(
        [str(x) for x in settings.IMG_THUMBNAIL_SIZE]
    ))
    img.save(".".join(chunks))


class UserTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.is_active)


class BaseModel(models.Model):
    create_datetime = models.DateTimeField(auto_now_add=True)
    update_datetime = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class Visitor(BaseModel):
    def __str__(self):
        return "Visitor (%d)" % self.pk

class RegisteredUser(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    MANUALLY_CREATED = "MANUALLY_CREATED"
    registration_provider = models.CharField(max_length=254)

    zip_code = models.DecimalField(max_digits=10, decimal_places=0, null=True)
    city = models.CharField(max_length=254, null=True)
    birth_year = models.DecimalField(max_digits=4, decimal_places=0, null=True)

    def __str__(self):
        return str(self.user)

class CityProject(BaseModel):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    description = models.TextField()
    image = models.ImageField()
    views = models.IntegerField(default=0)

    def __str__(self):
        return self.title


    def save(self, *args, **kwargs):
        """
        Quickly overriding the super()-function in order to also save a
        thumbnail.
        """
        super(CityProject, self).save(*args, **kwargs)
        if self.image is not None:
            createThumbnail(self.image.path)


class CityProjectVote(BaseModel):
    project = models.ForeignKey(CityProject, on_delete=models.CASCADE)
    vote = models.IntegerField(default=0)
    comment = models.TextField()
    visitor = models.ForeignKey(Visitor, on_delete=models.DO_NOTHING)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='unique_project_vote_per_visitor',
                fields=['project', "visitor"],
            )
        ]

    def __str__(self):
        return ("blank vote" if self.vote==0 else \
            "up vote" if self.vote>0 else "down vote")\
            + " (%s)" % self.visitor.pk


class CityProjectComment(BaseModel):
    project = models.ForeignKey(CityProject, on_delete=models.CASCADE)
    visitor = models.ForeignKey(Visitor, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,
        null=True)
    validated = models.BooleanField()
    name_displayed = models.BooleanField()
    comment = models.TextField()

    def __str__(self):
        return "Commentaire de %s (%s/%s) - %s" % (
            self.user,
            "validé" if self.validated else "non validé",
            "nom affiché" if self.name_displayed else "anonyme",
            (self.comment[:25] + '...') if len(self.comment) > 25 else self.comment,
        )


class Petition(BaseModel):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    description = models.TextField()
    image = models.ImageField(blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    views = models.IntegerField(default=0)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return "%s (%s)" % (self.title,
            "Approuvée" if self.approved else "Non approuvée"
        )

    def save(self, *args, **kwargs):
        """
        Quickly overriding the super()-function in order to also save a
        thumbnail.
        """
        super().save(*args, **kwargs)
        if self.image and hasattr(self.image, 'path'):
            createThumbnail(self.image.path)




class PetitionSignature(BaseModel):
    petition = models.ForeignKey(Petition, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s " % (str(self.user), self.petition.title)

class PetitionComment(BaseModel):
    petition = models.ForeignKey(Petition, on_delete=models.CASCADE)
    visitor = models.ForeignKey(Visitor, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,
        null=True)
    validated = models.BooleanField()
    name_displayed = models.BooleanField()
    comment = models.TextField()

    def __str__(self):
        return "Commentaire de %s (%s/%s) - %s" % (
            self.user,
            "validé" if self.validated else "non validé",
            "nom affiché" if self.name_displayed else "anonyme",
            (self.comment[:25] + '...') if len(self.comment) > 25 else self.comment,
        )
