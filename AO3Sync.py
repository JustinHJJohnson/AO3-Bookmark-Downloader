import sqlite3
from typing import List
import AO3T
import argparse
import toml


config = toml.load(f"./config.toml")

class LibraryBook(object):
    title: str
    lastModified: str
    
    def __init__(self, title: str, lastModified: str) -> None:
        self.title = title
        self.lastModified = lastModified
    
    def __str__(self):
        return f'{self.title} {self.lastModified}'


def arguments():
    parser = argparse.ArgumentParser("AO3Sync")
    parser.add_argument('-t', "--test", help="Testing flag", action='store_true')
    parser.add_argument('-d', '--dryrun', help="Fetch works but don't download", action='store_true')
    parser.add_argument('-a', '--all', help="Check all bookmarks, without this flag only the first page will be checked", action='store_true')
    return parser.parse_args()

def get_calibre_books() -> List[LibraryBook]:
    con = sqlite3.connect(config['calibre_db_path'])
    cur = con.cursor()
    res = cur.execute("SELECT title, timestamp FROM books")
    books = []
    for row in res:
        books.append(LibraryBook(*row))
    con.close()
    return books

def get_kavita_books() -> List[LibraryBook]:
    con = sqlite3.connect(config['kavita_db_path'])
    cur = con.cursor()
    res = cur.fetchmany
    res = cur.execute("SELECT TitleName, LastModified FROM Chapter")
    books = []
    for row in res:
        books.append(LibraryBook(*row))
    con.close()
    return books

def test_get_kavita_books() -> List[LibraryBook]:
    test_data = [
        LibraryBook("Quick Step", ""),
        LibraryBook("suck the rot right out of my bloodstream", ""),
        LibraryBook("I'm Up, I'm Up", ""),
        LibraryBook("A Fine Tradition", ""),
        LibraryBook("no one will love me like you again", ""),
        LibraryBook("Silver-Tongue", ""),
        LibraryBook("don't you know (i dream of you)", ""),
        LibraryBook("Kill your darlings", ""),
        LibraryBook("The Dekarios Folly", ""),
        LibraryBook("From the root", ""),
        LibraryBook("Fool's luck", ""),
        LibraryBook("fire in my brain and i'm burning up", ""),
        LibraryBook("Someone Else's Soul", ""),
        LibraryBook("Memories of the Seasons", ""),
        LibraryBook("discounted", ""),
        LibraryBook("10 Ways to Say I Love You", ""),
        LibraryBook("Gimmie Love", ""),
        LibraryBook("New Game Plus", ""),
        LibraryBook("New Miracle", ""),
        LibraryBook("", ""),
    ]
    return test_data

def get_ao3_bookmarks(get_all_bookmarks=False) -> List[AO3T.Work]:
    session = AO3T.Session(config['ao3_username'], config['ao3_password'])
    bookmarks = session.get_bookmarks() if get_all_bookmarks else session.get_bookmarks(pages=1)
    for bookmark in bookmarks:
        bookmark.set_session(session)
    return bookmarks

def sync_library_and_bookmarks(bookmarks: List[AO3T.Work], library_books: List[LibraryBook]) -> List[AO3T.Work]:
    library_titles = []
    for book in library_books:
        library_titles.append(book.title)
    missing_works = bookmarks.copy()

    for bookmark_work in bookmarks:
        for library_book_title in library_titles:
            if library_book_title == bookmark_work.title:
                missing_works.remove(bookmark_work)
                break

    return missing_works

def load_works_threaded(works: List[AO3T.Work]):
    threads = []
    for work in works:
        threads.append(work.reload(threaded=True))
    for thread in threads:
        thread.join()

def load_works(works: List[AO3T.Work], load_chapters=True):
    for work in works:
        work.reload(load_chapters=load_chapters)

def printWorks(works: List[AO3T.Work], collection=False):
    if (collection):
        for work in works: print(f'{work.title} - {work.series}')
    else: 
        for work in works: print(f'{work.title}')

def main():
    args = arguments()
    kavita_books = get_kavita_books()
    bookmarks = get_ao3_bookmarks(args.all)
    missing_works = sync_library_and_bookmarks(bookmarks, kavita_books)
    print(f'The following works are bookmarked, but not downloaded:')
    printWorks(missing_works)
    if (not args.dryrun):
        load_works(missing_works)
        for work in missing_works:
            print(f"downloading {work.title}")
            with open(f"{config['download_path']}/{work.title}.epub", "wb") as file:
                file.write(work.download("EPUB"))
                file.close()


if __name__ == "__main__":
    main()