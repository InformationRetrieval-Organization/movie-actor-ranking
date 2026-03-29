from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Movie(SQLModel, table=True):
    __tablename__ = "Movie"

    id: Optional[int] = Field(default=None, primary_key=True)
    imdbId: Optional[int] = Field(default=None, unique=True)
    title: str
    coverUrl: Optional[str] = None

    roles: list["Role"] = Relationship(back_populates="movie")
    scripts: list["Script"] = Relationship(back_populates="movie")


class Actor(SQLModel, table=True):
    __tablename__ = "Actor"

    id: Optional[int] = Field(default=None, primary_key=True)
    imdbId: Optional[int] = Field(default=None, unique=True)
    name: str
    headshotUrl: Optional[str] = None

    classifiers: list["ActorClassifier"] = Relationship(back_populates="actor")
    roles: list["Role"] = Relationship(back_populates="actor")


class Role(SQLModel, table=True):
    __tablename__ = "Role"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    movieId: int = Field(foreign_key="Movie.id", ondelete="CASCADE")
    actorId: int = Field(foreign_key="Actor.id", ondelete="CASCADE")

    actor: Optional[Actor] = Relationship(back_populates="roles")
    movie: Optional[Movie] = Relationship(back_populates="roles")
    scripts: list["Script"] = Relationship(back_populates="role")


class Script(SQLModel, table=True):
    __tablename__ = "Script"

    id: Optional[int] = Field(default=None, primary_key=True)
    dialogue: str
    processedDialogue: Optional[str] = None
    movieId: int = Field(foreign_key="Movie.id", ondelete="CASCADE")
    roleId: int = Field(foreign_key="Role.id", ondelete="CASCADE")

    movie: Optional[Movie] = Relationship(back_populates="scripts")
    role: Optional[Role] = Relationship(back_populates="scripts")


class ActorClassifier(SQLModel, table=True):
    __tablename__ = "ActorClassifier"

    id: Optional[int] = Field(default=None, primary_key=True)
    actorId: int = Field(foreign_key="Actor.id", ondelete="CASCADE")
    loveScore: Optional[float] = None
    joyScore: Optional[float] = None
    angerScore: Optional[float] = None
    sadnessScore: Optional[float] = None
    surpriseScore: Optional[float] = None
    fearScore: Optional[float] = None

    actor: Optional[Actor] = Relationship(back_populates="classifiers")
