from djongo import models


class Category(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=4000, null=True, blank=True)

    def __str__(self):
        return self.name

    objects = models.DjongoManager()


class Account(models.Model):
    ACCOUNT_TYPE_SAVINGS = "SAVINGS"
    ACCOUNT_TYPE_CURRENT = "CURRENT"
    ACCOUNT_TYPE_LOAN = "LOAN"
    ACCOUNT_TYPE_LENDING = "LENDING"

    name = models.CharField(max_length=128)
    description = models.CharField(max_length=4000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    balance = models.FloatField(default=0.0)
    commitment = models.FloatField(default=0.0)
    account_type = models.CharField(max_length=32, choices=[
        (ACCOUNT_TYPE_SAVINGS, ACCOUNT_TYPE_SAVINGS),
        (ACCOUNT_TYPE_CURRENT, ACCOUNT_TYPE_CURRENT),
        (ACCOUNT_TYPE_LOAN, ACCOUNT_TYPE_LOAN),
        (ACCOUNT_TYPE_LENDING, ACCOUNT_TYPE_LENDING)
    ], default="CURRENT")

    closed = models.BooleanField(default=False)

    def increment_balance(self, value):
        self.balance = self.balance + value
        self.save(update_fields=["balance"])

    def increment_commitment(self, value):
        self.commitment=self.commitment + value
        self.save(update_fields=["commitment"])

    def __str__(self):
        return "{}, Current Balance: {}, Commitments: {}, Net Balance: ".format(
            self.name,
            self.balance,
            self.commitment,
            self.balance - self.commitment
        )

    objects = models.DjongoManager()


class Commitment(models.Model):
    TRANSACTION_TYPE_INCOME = "INCOME"
    TRANSACTION_TYPE_EXPENSE = "EXPENSE"

    amount = models.FloatField(default=0.0)
    account = models.ForeignKey(Account, related_name="commitments", on_delete=models.CASCADE)
    description = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, related_name="commitments", on_delete=models.DO_NOTHING)
    expectedDate = models.DateField()
    archived = models.BooleanField(default=False)

    transaction_type = models.CharField(max_length=32, choices=[
        (TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_INCOME),
        (TRANSACTION_TYPE_EXPENSE, TRANSACTION_TYPE_EXPENSE)
    ], )

    original_value = models.FloatField(default=0)

    objects = models.DjongoManager()

    def save(self, *args, **kwargs):
        self.original_value = self.amount
        if self.transaction_type == Transaction.TRANSACTION_TYPE_EXPENSE:
            self.original_value = self.original_value * -1

        if self.pk is None:
            self.account.increment_commitment(self.original_value)
        else:
            existing = Transaction.objects.get(pk=self.pk)
            if existing.account_id != self.account_id:
                existing.account.increment_balance(existing.original_value)
                self.account.increment_commitment(self.original_value)
            elif existing.original_value != self.original_value:
                self.account.increment_commitment(self.original_value - existing.original_value)

        super(Commitment, self).save(*args, **kwargs)

    def __str__(self):
        return "Account: {}, Commitment: {}, {}".format(self.account, self.original_value, self.description)

    def delete(self, *args, **kwargs):
        self.account.increment_commitment(self.original_value * -1)
        super(Transaction, self).delete(*args, **kwargs)


class Transaction(models.Model):
    TRANSACTION_TYPE_INCOME = "INCOME"
    TRANSACTION_TYPE_EXPENSE = "EXPENSE"

    amount = models.FloatField(default=0.0)
    account = models.ForeignKey(Account, related_name="transactions", on_delete=models.CASCADE)
    description = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, related_name="transactions", on_delete=models.SET_NULL, null=True)
    commitment = models.ForeignKey(Commitment, related_name="transactions", on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=32, choices=[
        (TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_INCOME),
        (TRANSACTION_TYPE_EXPENSE, TRANSACTION_TYPE_EXPENSE)
    ],)

    original_value = models.FloatField(default=0)

    objects = models.DjongoManager()

    def save(self, *args, **kwargs):
        self.original_value = self.amount
        if self.transaction_type == Transaction.TRANSACTION_TYPE_EXPENSE:
            self.original_value = self.original_value * -1

        if self.pk is None:
            self.account.increment_balance(self.original_value)
        else:
            existing = Transaction.objects.get(pk=self.pk)
            if existing.account_id != self.account_id:
                existing.account.increment_balance(existing.original_value)
                self.account.increment_balance(self.original_value)
            elif existing.original_value != self.original_value:
                self.account.increment_balance(self.original_value - existing.original_value)

        super(Transaction, self).save(*args, **kwargs)

    def __str__(self):
        return "Account: {}, Transaction Amount: {}".format(self.account.name, self.original_value)

    def delete(self, *args, **kwargs):
        self.account.increment_balance(self.original_value * -1)
        super(Transaction, self).delete(*args, **kwargs)

