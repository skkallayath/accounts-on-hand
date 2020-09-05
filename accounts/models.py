from django.db.models import F
from djongo import models


class Category(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=4000, null=True, blank=True)


class Account(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=4000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    balance = models.FloatField(default=0.0)
    commitment = models.FloatField(default=0.0)
    account_type = models.CharField(choices=[("SAVINGS", "SAVINGS"), ("CURRENT", "CURRENT")], default="CURRENT")

    def increment_balance(self, value):
        Account.objects.filter(pk=self.pk).update(balance=F('balance')+value)

    def increment_commitment(self, value):
        Account.objects.filter(pk=self.pk).update(commitment=F('commitment')+value)


class Commitment(models.Model):
    TRANSACTION_TYPE_INCOME = "INCOME"
    TRANSACTION_TYPE_EXPENSE = "EXPENSE"

    amount = models.FloatField(default=0.0)
    account = models.ForeignKey(Account, related_name="account", on_delete=models.CASCADE)
    description = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, related_name="category", on_delete=models.DO_NOTHING)
    expectedDate = models.DateField()
    archived = models.BooleanField(default=False)

    transaction_type = models.CharField(choices=[
        (TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_INCOME),
        (TRANSACTION_TYPE_EXPENSE, TRANSACTION_TYPE_EXPENSE)
    ], )

    original_value = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        self.original_value = self.amount
        if self.transaction_type == Transaction.TRANSACTION_TYPE_EXPENSE:
            self.original_value = self.original_value * -1

        if self.pk is None:
            self.account.increment_commitment(self.original_value, self.transaction_type)
        else:
            existing = Transaction.objects.get(pk=self.pk)
            if existing.account_id != self.account_id:
                existing.account.increment_balance(existing.amount * -1)
                self.account.increment_commitment(self.original_value)
            elif existing.original_value != self.original_value:
                self.account.increment_commitment(self.original_value - existing.original_value)

        super(Commitment, self).save(*args, **kwargs)


class Transaction(models.Model):
    TRANSACTION_TYPE_INCOME = "INCOME"
    TRANSACTION_TYPE_EXPENSE = "EXPENSE"

    amount = models.FloatField(default=0.0)
    account = models.ForeignKey(Account, related_name="transaction", on_delete=models.CASCADE)
    description = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, related_name="transaction", on_delete=models.SET_NULL, null=True)
    commitment = models.ForeignKey(Commitment, related_name="transaction", on_delete=models.SET_NULL, null=True)
    transaction_type = models.CharField(choices=[
        (TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_INCOME),
        (TRANSACTION_TYPE_EXPENSE, TRANSACTION_TYPE_EXPENSE)
    ],)

    original_value = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        self.original_value = self.amount
        if self.transaction_type == Transaction.TRANSACTION_TYPE_EXPENSE:
            self.original_value = self.original_value * -1

        if self.pk is None:
            self.account.increment_balance(self.original_value, self.transaction_type)
        else:
            existing = Transaction.objects.get(pk=self.pk)
            if existing.account_id != self.account_id:
                existing.account.increment_balance(existing.amount * -1)
                self.account.increment_balance(self.original_value)
            elif existing.original_value != self.original_value:
                self.account.increment_balance(self.original_value - existing.original_value)

        super(Transaction, self).save(*args, **kwargs)
