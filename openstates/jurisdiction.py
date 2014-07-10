from pupa.scrape import Jurisdiction, Organization
from openstates.base import OpenstatesBaseScraper
from openstates.people import OpenstatesPersonScraper
from openstates.events import OpenstatesEventScraper
from openstates.bills import OpenstatesBillScraper

POSTS = {
    'ak': {'lower': range(1, 41), 'upper': (chr(n) for n in range(65, 85))},
    'al': {'lower': range(1, 106), 'upper': range(1, 36)},
    'nc': {'lower': range(1, 121), 'upper': range(1, 51)},
}

def chamber_name(state, chamber):
    if state in ('ne', 'dc', 'pr'):
        raise ValueError(state)

    if chamber == 'lower':
        if state in ('ca', 'ny', 'wi'):
            return 'State Assembly'
        elif state in ('md', 'va', 'wv'):
            return 'House of Delegates'
        elif state == 'nv':
            return 'Assembly'
        elif state == 'nj':
            return 'General Assembly'
        else:
            return 'House of Representatives'   # 41 of these
    elif chamber == 'upper':
        if state in ('ca', 'ga', 'la', 'ms', 'ny', 'or', 'pa', 'wa', 'wi'):
            return 'State Senate'
        else:
            return 'Senate'


def make_jurisdiction(a_state):

    osbs = OpenstatesBaseScraper(None, None)
    metadata = osbs.api('metadata/{}?'.format(a_state))

    # timezone
    # chambers.title

    leg_sessions = []
    for td in metadata['terms']:
        for s in td['sessions']:
            session = {'identifier': s,
                       'name': metadata['session_details'][s]['display_name'],
                       'start_date': metadata['session_details'][s].get('start_date', '')[:10],
                       'end_date': metadata['session_details'][s].get('end_date', '')[:10],
                      }
            leg_sessions.append(session)

    # make scrapers
    class PersonScraper(OpenstatesPersonScraper):
        state = a_state
    class BillScraper(OpenstatesBillScraper):
        state = a_state
    class EventScraper(OpenstatesEventScraper):
        state = a_state

    class StateJuris(Jurisdiction):
        division_id = 'ocd-division/country:us/state:' + a_state
        classification = 'government'
        name = metadata['name']
        scrapers = {'people': PersonScraper,
                    'bills': BillScraper,
                    #'events': EventScraper,
                   }
        parties = [{'name': 'Republican'},
                   {'name': 'Democratic'},
                   {'name': 'Independent'},
                  ]
        legislative_sessions = leg_sessions

        def get_organizations(self):
            legislature = Organization(metadata['legislature_name'], classification='legislature')
            yield legislature
            executive = Organization(metadata['name'] + ' Executive Branch',
                                     classification='executive')

            for otype in ('upper', 'lower'):
                if otype in metadata['chambers']:
                    org = Organization(metadata['name'] + ' ' + chamber_name(a_state, otype),
                                       classification=otype, parent_id=legislature._id)
                    for post in POSTS[a_state][otype]:
                        org.add_post(str(post), metadata['chambers'][otype]['title'])
                    yield org

    return StateJuris