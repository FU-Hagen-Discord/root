import io
import uuid
from datetime import datetime, timedelta

import discord
from discord import Colour
from peewee import *
from peewee import ModelSelect

db = SqliteDatabase("root.db")


class BaseModel(Model):
    class Meta:
        database = db


class Poll(BaseModel):
    question = CharField()
    author = IntegerField()
    channel = IntegerField()
    message = IntegerField()

    def get_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Umfrage", description=self.question)
        embed.add_field(name="Erstellt von", value=f'<@!{self.author}>', inline=False)
        embed.add_field(name="\u200b", value="\u200b", inline=False)

        for choice in self.choices:
            name = f'{choice.emoji}  {choice.text}'
            value = f'{len(choice.choice_chosen)}'

            embed.add_field(name=name, value=value, inline=False)

        participants = {str(choice_chosen.member_id): 1 for choice_chosen in
                        PollChoiceChosen.select().join(PollChoice, on=PollChoiceChosen.poll_choice).where(
                            PollChoice.poll == self)}

        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Anzahl der Teilnehmer an der Umfrage", value=f"{len(participants)}", inline=False)

        return embed


class PollChoice(BaseModel):
    poll = ForeignKeyField(Poll, backref='choices')
    text = CharField()
    emoji = CharField()


class PollChoiceChosen(BaseModel):
    poll_choice = ForeignKeyField(PollChoice, backref='choice_chosen')
    member_id = IntegerField()


class Appointment(BaseModel):
    channel = IntegerField()
    message = IntegerField()
    date_time = DateTimeField()
    reminder = IntegerField()
    title = CharField()
    description = CharField()
    author = IntegerField()
    recurring = IntegerField()
    reminder_sent = BooleanField()
    uuid = UUIDField(default=uuid.uuid4())

    def get_embed(self, state: int) -> discord.Embed:
        attendees = self.attendees
        description = (f"- Durch Klicken auf Anmelden erhältst du eine Benachrichtigung zum Beginn des Termins"
                       f"{f', sowie {self.reminder} Minuten vorher' if self.reminder > 0 else f''}.\n"
                       f"- Durch Klicken auf Abmelden nimmst du deine vorherige Anmeldung wieder zurück und wirst "
                       f"nicht benachrichtigt.") if state != 2 else ""
        emoji = "📅" if state == 0 else ("📣" if state == 1 else "✅")
        embed = discord.Embed(title=f"{emoji} __{self.title}__ {'findet jetzt statt.' if state == 2 else ''}",
                              description=description)

        embed.color = Colour.green() if state == 0 else Colour.yellow() if state == 1 else 19607

        if len(self.description) > 0:
            embed.add_field(name="Beschreibung", value=self.description, inline=False)

        embed.add_field(name="Startzeitpunkt", value=self.get_start_time(state), inline=False)
        if self.reminder > 0 and state == 0:
            embed.add_field(name="Erinnerung", value=f"{self.reminder} Minuten vor dem Start", inline=False)
        if self.recurring > 0:
            embed.add_field(name="Wiederholung", value=f"Alle {self.recurring} Tage", inline=False)
        if len(attendees) > 0:
            embed.add_field(name=f"Teilnehmerinnen ({len(attendees)})",
                            value=",".join([f"<@{attendee.member_id}>" for attendee in attendees]))

        return embed

    def remind_at(self) -> datetime:
        if self.reminder_sent:
            return self.date_time
        elif datetime.now() >= self.date_time:
            Appointment.update(reminder_sent=True).where(Appointment.id == self.id).execute()
            self.reminder_sent = True
            return self.date_time
        else:
            return self.date_time - timedelta(minutes=self.reminder)

    def get_start_time(self, state) -> str:
        if state == 0:
            return f"<t:{int(self.date_time.timestamp())}:F>"

        return f"<t:{int(self.date_time.timestamp())}:F> (<t:{int(self.date_time.timestamp())}:R>)"

    def get_ics_file(self):
        fmt = "%Y%m%dT%H%M"
        appointment = f"BEGIN:VCALENDAR\n" \
                      f"PRODID:Boty McBotface\n" \
                      f"VERSION:2.0\n" \
                      f"BEGIN:VTIMEZONE\n" \
                      f"TZID:Europe/Berlin\n" \
                      f"BEGIN:DAYLIGHT\n" \
                      f"TZOFFSETFROM:+0100\n" \
                      f"TZOFFSETTO:+0200\n" \
                      f"TZNAME:CEST\n" \
                      f"DTSTART:19700329T020000\n" \
                      f"RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3\n" \
                      f"END:DAYLIGHT\n" \
                      f"BEGIN:STANDARD\n" \
                      f"TZOFFSETFROM:+0200\n" \
                      f"TZOFFSETTO:+0100\n" \
                      f"TZNAME:CET\n" \
                      f"DTSTART:19701025T030000\n" \
                      f"RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10\n" \
                      f"END:STANDARD\n" \
                      f"END:VTIMEZONE\n" \
                      f"BEGIN:VEVENT\n" \
                      f"DTSTAMP:{datetime.now().strftime(fmt)}00Z\n" \
                      f"UID:{self.uuid}\n" \
                      f"SUMMARY:{self.title}\n"
        appointment += f"RRULE:FREQ=DAILY;INTERVAL={self.recurring}\n" if self.recurring else f""
        appointment += f"DTSTART;TZID=Europe/Berlin:{self.date_time.strftime(fmt)}00\n" \
                       f"DTEND;TZID=Europe/Berlin:{self.date_time.strftime(fmt)}00\n" \
                       f"TRANSP:OPAQUE\n" \
                       f"BEGIN:VALARM\n" \
                       f"ACTION:DISPLAY\n" \
                       f"TRIGGER;VALUE=DURATION:-PT{self.reminder}M\n" \
                       f"DESCRIPTION:{self.description}\n" \
                       f"END:VALARM\n" \
                       f"END:VEVENT\n" \
                       f"END:VCALENDAR"
        ics_file = io.BytesIO(appointment.encode("utf-8"))
        return ics_file


class Attendee(BaseModel):
    appointment = ForeignKeyField(Appointment, backref='attendees')
    member_id = IntegerField()


class Topic(BaseModel):
    channel = IntegerField()
    name = CharField()

    @classmethod
    def get_topics(cls, channel: int, topic: str = None) -> ModelSelect:
        topics: ModelSelect = cls.select().where(Topic.channel == channel)
        return topics.where(Topic.name == topic) if topic else topics

    @classmethod
    def has_links(cls, channel: int, topic: str = None) -> bool:
        for topic in cls.get_topics(channel, topic=topic):
            if len(list(topic.links)) > 0:
                return True

        return False

    def append_field(self, embed: discord.Embed):
        value = ""
        for link in self.links:
            value += f"- [{link.title}]({link.link})\n"

        embed.add_field(name=self.name.capitalize(), value=value, inline=False)


class Link(BaseModel):
    link = CharField()
    title = CharField()
    topic = ForeignKeyField(Topic, backref='links')


class Timer(BaseModel):
    name = CharField()
    status = CharField()
    working_time = IntegerField()
    break_time = IntegerField()
    remaining = IntegerField()
    guild = IntegerField()
    channel = IntegerField()
    message = IntegerField()

    def create_embed(self):
        color = discord.Colour.green() if self.status == "Arbeiten" else 0xFFC63A if self.status == "Pause" else discord.Colour.red()
        zeiten = f"{self.working_time} Minuten Arbeiten\n{self.break_time} Minuten Pause"
        remaining_value = f"{self.remaining} Minuten"
        endzeit = (datetime.now() + timedelta(minutes=self.remaining)).strftime("%H:%M")
        end_value = f" [bis {endzeit} Uhr]" if self.status != "Beendet" else ""
        angemeldet_value = ", ".join([f"<@{attendee.member}>" for attendee in self.attendees])

        embed = discord.Embed(title=self.name,
                              color=color)
        embed.add_field(name="Status:", value=self.status, inline=False)
        embed.add_field(name="Zeiten:", value=zeiten, inline=False)
        embed.add_field(name="verbleibende Zeit:", value=remaining_value + end_value, inline=False)
        embed.add_field(name="angemeldete User:", value=angemeldet_value if len(angemeldet_value) > 0 else "-",
                        inline=False)

        return embed


class TimerAttendee(BaseModel):
    timer = ForeignKeyField(Timer, backref="attendees")
    member = IntegerField()


class Command(BaseModel):
    command = CharField(unique=True)
    description = CharField()


class CommandText(BaseModel):
    text = CharField()
    command = ForeignKeyField(Command, backref="texts")

class SprachRohr(BaseModel):
    url = CharField()
    year = IntegerField()
    issue = CharField()

class News(BaseModel):
    link = CharField()
    date = CharField()

db.create_tables([Poll, PollChoice, PollChoiceChosen, Appointment, Attendee, Topic, Link, Timer, TimerAttendee, Command,
                  CommandText, SprachRohr, News], safe=True)
