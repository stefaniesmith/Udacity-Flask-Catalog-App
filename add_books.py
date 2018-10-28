from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Book, User
import logging


engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create dummy users
User1 = User(name="John Smith", email="johnsmith@noemail.com")
session.add(User1)
session.commit()

User2 = User(name="Mary Brown", email="marybrown@noemail.com")
session.add(User2)
session.commit()

User2 = User(name="Jill Jones", email="jilljones@noemail.com")
session.add(User2)
session.commit()

# Create categories
action = Category(name="Action/Adventure")
drama = Category(name="Drama")
mystery = Category(name="Mystery")
nonfiction = Category(name="Non-Fiction")
reference = Category(name="Reference")
romance = Category(name="Romance")
scifi = Category(name="Science Fiction")

for c in [action, drama, mystery, nonfiction, reference, romance, scifi]:
    session.add(c)
    session.commit()

# Action/Adventure books
book1 = Book(
    title="The Count of Monte Cristo",
    author="Alexandre Dumas",
    description=("A revenge thriller set in France, this is the story of "
                 "Edmond Dantes, a merchant sailor, who is thrown in prison "
                 "for a crime he did not commit. While imprisoned, he learns "
                 "of a great treasure hidden on the Isle of Monte Cristo. "
                 "After escaping from prison, he finds the treasure and "
                 "uses his new found wealth to destroy those responsible "
                 "for his imprisonment."),
    category=action,
    user_id=1)

session.add(book1)
session.commit()

# Romance books
book2 = Book(
    title="Sense and Sensibility",
    author="Jane Austen",
    description=("The story of the Dashwood sisters, set in England in "
                 "the 1790s, as they experience love and heartbreak."),
    category=romance,
    user_id=2)

session.add(book2)
session.commit()

book3 = Book(
    title="Jane Eyre",
    author="Charlotte Bronte",
    description=("The story of Jane Eyre, a young woman who takes the job "
                 "of a governess at Thornfield Hall in northern England "
                 "and falls in love with her employer."),
    category=romance,
    user_id=3)

session.add(book3)
session.commit()

# Mystery books
book4 = Book(
    title="Murder on the Orient Express",
    author="Agatha Christie",
    description=("Detective Hercule Poirot investigates the murder of a "
                 "fellow passenger aboard the luxurious Orient Express, "
                 "as it travels from the Middle East to Europe."),
    category=mystery,
    user_id=1)

session.add(book4)
session.commit()

book5 = Book(
    title="A Study in Scarlet",
    author="Arthur Conan Doyle",
    description=("Sherlock Holmes and Dr John Watson investigate the "
                 "murder of a man found in a south London home."),
    category=mystery,
    user_id=3)

session.add(book5)
session.commit()

# Science fiction books
book6 = Book(
    title="The Time Machine",
    author="H. G. Wells",
    description=("An English scientist and inventor uses a time machine "
                 "to travel 800,000 years into the future."),
    category=scifi,
    user_id=2)

session.add(book6)
session.commit()

logging.info("Successfully added books!")
