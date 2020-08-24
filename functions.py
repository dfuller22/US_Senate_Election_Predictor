def wiki_senate_scraper():
    import pandas as pd
    import numpy as np
    import requests
    from bs4 import BeautifulSoup
    
    ## Starting page + Q.C. of response
    start_url = 'https://en.wikipedia.org/wiki/List_of_United_States_Senate_elections'
    start_resp = requests.get(start_url)
    print(f'Starting Response: {start_resp}')
    
    ## Creating soup + pulling all links for senate elections after 17th amendment
    start_soup = BeautifulSoup(start_resp.text, 'html.parser')
    start_links = start_soup.findAll('a')
    start_sen_links = start_links[78:134] ## Previously located
    
    ## Base of url for all senate election pages
    base_url = 'https://en.wikipedia.org'
    
    ## Loop same process for all links + storage
    yr_dfs = {}
    yr_tocs = {}
    count = 0
    for link in start_sen_links:

        ## Q.C during execute
        count += 1
        if count in [25, 50]:
            print('Checkpoint! (25 loops)')
        
        ## Collecting strings for use
        end_url = link.get('href')
        year = link.get_text()
        full_url = base_url + end_url
        
        ## Making soup + collecting all tables
        link_resp = requests.get(full_url)
        link_soup = BeautifulSoup(link_resp.text, 'html.parser')
        link_tables = link_soup.findAll('table', attrs={'class': ['wikitable', 'infobox vevent', 'infobox']})
        
        ## Collecting list of states with elections in each year
        link_toc = link_soup.find('div', attrs={'id':'toc'})
        link_toc = link_toc.findAll('a', href=is_state)
        toc_list = [tag.get('href').replace('#', '') for tag in link_toc]
        
        ## Converting to dataframe + storage
        elect_df = pd.read_html(str(link_tables))
        yr_dfs[year] = elect_df
        yr_tocs[year] = toc_list
    
    print(f'Total pages scraped: {count}')
    return yr_dfs, yr_tocs

## https://www.crummy.com/software/BeautifulSoup/bs4/doc/#kinds-of-filters

def is_state(href):
    states_list = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 
                   'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
                   'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas',
                   'Kentucky', 'Louisiana', 'Maine', 'Maryland',
                   'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi',
                   'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New_Hampshire',
                   'New_Jersey', 'New_Mexico', 'New_York', 'North_Carolina',
                   'North_Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania',
                   'Rhode_Island', 'South_Carolina', 'South_Dakota',
                   'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia',
                   'Washington', 'West_Virginia', 'Wisconsin', 'Wyoming']
    for state in states_list:
        if state in href:
            return href

def election_collector(dict_tables, dict_lists, yr_end='2020'):
    
    ## Requirement of proper dictionaries
    if dict_tables.keys() != dict_lists.keys():
        print('**WARNING**')
        print('Keys do not match in dictionaries passed. Adjust and try again.')
        return '***'*10
    
    ## Containers for results
    coll_elects = {}
    
    ## List creation for looping through dicts
    yr_list = list(dict_lists.keys())
    
    ## Looping + storage
    for year in yr_list:
        if year == yr_end:
            break
        print('***'*10)
        print(f"Collecting {year}'s elections...")
        yr_tables = dict_tables[year]
        yr_toc = dict_lists[year]
        
        ## Creating containers to further separate data
        yr_sum_ldrs = yr_tables[2]
        most_tables = yr_tables[3:]
        yr_summary = []
        yr_states = []
        count = 0
        
        for i, df in enumerate(most_tables):
            if count < 1:
                if year == '2018':
                    count += 1
                    yr_summary.append(yr_tables[10])
                    yr_summary.append(yr_tables[11])
                    continue
                elif df.shape[1] is 6 and most_tables[i+1].shape[1] is 6:
                    count += 1
                    yr_summary.append(most_tables[i])
                    yr_summary.append(most_tables[i+1])
                    continue
                elif df.shape[1] is 6:
                    count += 1
                    yr_summary.append(most_tables[i])
            
            if df.shape[1] in [4,5,6] and df.shape[0] <= 15:
                yr_states.append(most_tables[i])
        
        coll_elects[year] = [yr_sum_ldrs, yr_summary, yr_states]
        
    print('\n')
    print('---'*20)
    disp_yrs = list(coll_elects.keys())
    print(f'Collection Complete: Data is for {disp_yrs[0]} - {disp_yrs[-1]}')
    print('---'*20)
    return coll_elects

def yr_summary_collector(election_collection):
    import pandas as pd 

    ## Container for results
    yr_summaries = {}
    
    ## Extraction as a list for iteration
    for year in election_collection:
        elect_list = [election_collection[year]]
        
        ## Looping through year's collection
        for coll in elect_list:
            ## Container for mid-results
            holder = []
            ## Looping through each table in 'year summary' group
            for table in coll[1]:
                ## Variable to filter unwanted tables out
                has_elected = False
                ## Looping through each row in 'results' column (idx 4)
                for u in table.iloc[:,4]:
                ## Checking for str to 'flag' table as collectable
                    if isinstance(u, str) and 'elected' in u:
                        has_elected = True
                if has_elected == True:
                    holder.append(table)
            ## Check if multiple tables in 'year summary' group
            if len(holder) > 1:
                is_match = holder[0].iloc[1,:] == holder[1].iloc[1,:]
                ## Check if tables have matching headers for special 
                ## election years + storage
                if is_match.sum() in [2,3]:
                    fin_tab = holder[1].append(holder[0], ignore_index=True)
                    yr_summaries[year] = fin_tab
            ## Storage of non-special election years
            else:
                try:
                    yr_summaries[year] = holder.pop()
                except:
                    continue
        
    return yr_summaries

def ref_tabler(summary_df, mod_df=True):
    import pandas as pd
    
    ## Containers for mid-results
    st_list = []
    sntr_list = []
    prty_list = []
    
    ## Looping through states' names
    for state in summary_df['State']:
        ## Check/replace spaces with '_' + storage
        if ' ' in state:
            fmt_state = state.replace(' ', '_')
            st_list.append(fmt_state)
        else:
            st_list.append(state)
    ## Looping + storing senator names
    for name in summary_df['Senator']:
        sntr_list.append(name)

    ## Looping + storing parties
    for party in summary_df['Party']:
        prty_list.append(party)

    ## Dataframe with Sentors as index + states as values
    state_ref_df = pd.DataFrame({'State_id':st_list, 'Incumbent':sntr_list, 'Party':prty_list})
    #state_ref_df.columns = ['State_id']
    
    ## Modifying list of states to that of the ref table OR not + return
    if mod_df:
        summary_df['State'] = st_list
        return summary_df, state_ref_df
    else:
        return state_ref_df

def master_tabler(yr_summary_dict):
    import pandas as pd
    import regex

    holder = []

    for year in yr_summary_dict:
        holder.append(yr_summary_dict[year][1])

    name_lookup_df = pd.concat(holder, ignore_index=True)
    name_lookup_df['Terms_in_office'] = 0
    name_lookup_df['Cln_name'] = name_lookup_df['Incumbent'].map(lambda x: regex.sub(r'([A-z]{1,2}\.)\s?', '', x).strip())

    for cand in name_lookup_df['Incumbent']:
        count = 0
        for i, name in zip(name_lookup_df.index, name_lookup_df['Incumbent']):
            if name == cand:
                count += 1
                name_lookup_df.at[i, 'Terms_in_office'] = count
    
    return name_lookup_df

def yr_sum_formatter(yr_sum_dict, ref_table=True):
    import pandas as pd

    ## Container for results + column helper
    res_dict = {}
    df_cols = ['State', 'Senator', 'Party', 'Electoral_History', 'Results', 'Candidates']
    
    ## Looping to each year's summary table
    for year in yr_sum_dict:
        ## Setting copy to modify + setting columns + rows to remove
        summary_df = yr_sum_dict[year].copy()
        summary_df.columns = df_cols
        drop_1 = summary_df.iloc[0]
        drop_2 = summary_df.iloc[1]
        
        ## Removing rows that match 'drop_' rows (former column info)
        for idx, row in summary_df.iterrows():
            if drop_1.equals(row):
                summary_df.drop(idx, inplace=True)
            elif drop_2.equals(row):
                summary_df.drop(idx, inplace=True)
        
        ## Resetting index to rangeIndex
        summary_df.reset_index(drop=True, inplace=True)
        
        ## Storing State-Senator lookup dataframe OR not
        if ref_table:
            summary_df, state_ref_df = ref_tabler(summary_df)
            state_ref_df['Year'] = year
            res_dict[year] = [summary_df, state_ref_df]    
        else:
            res_dict[year] = summary_df
        
    ## Return results
    return res_dict

def st_election_cleaner(dict_of_lists, exclude=[]):
    st_gens_cln = {}

    for year in dict_of_lists:
        if year in exclude:
            continue
        coll = dict_of_lists[year]
        holder = []
        
        for table in coll:
            if table.shape[1] in [5,6]:
                try:
                    table_cln = st_election_formatter(table)
                    holder.append(table_cln)
                except KeyError as e:
                    print(f'Error!! {e}')
                    print(f'Year affected: {year}')
                    display(table)
        
        st_gens_cln[year] = holder
        
    return st_gens_cln

def st_election_collector(election_collection):
    
    ## Container for results
    st_elects = {}
    
    ## Extraction of each year's state elections
    for year in election_collection:
        elect_list = election_collection[year]
        st_elects[year] = elect_list[2]
        
    return st_elects

def st_election_formatter(df):
    import pandas as pd 

    df_cln = df.copy()
    
    cols = ['Drop']
    cols.extend(df_cln.iloc[0,:-1])
    df_cln.columns = cols
    df_cln.drop(0, inplace=True)
    
    for i, v, na in zip(df_cln.index, df_cln['Drop'], df_cln['Drop'].isna()):
        if not na:
            df_cln[v] = df_cln['Party'][i]
            
    df_cln.drop(columns='Drop', inplace=True)
    
    for col in df_cln:
        df_cln_height = df_cln.shape[0]
        df_cln_nNA = df_cln[col].isna().sum()
        
        if df_cln_nNA == df_cln_height:
            df_cln.drop(columns=col, inplace=True)
            
        elif df_cln_height == 2 and df_cln_nNA > 0:
            df_cln.dropna(axis=0, inplace=True)
            
        elif df_cln_nNA == (df_cln_height-1) and df_cln_nNA > 0:
            df_cln.drop(columns=col, inplace=True)
            
        elif df_cln_nNA > 0:
            for i, v, na in zip(df_cln.index, df_cln[col], df_cln[col].isna()):
                if na:
                    df_cln.drop(i, inplace=True)
    
    return df_cln

def table_checker(list_=None, dict_=None):
    if not list_ and not dict_:
        print('---'*20)
        print('Error! Must enter either List or Dictionary.')
        print('---'*20)
        
    if list_ and not dict_:
        slice_ = input('Index(ices) to slice:')
        try:
            res = list_[slice_]
            return res
        except:
            print(f'Error! List slice {slice_}.')
            
    if dict_ and not list_:
        key_ = input('Key to pull:')
        try:
            res = dict_[key_]
            return res
        except:
            print(f'Error! Dictionary key {key_}')

def st_election_aggregator(dict_of_lists):
    import pandas as pd 

    ## Container for results
    res_dict = {}
    
    ## Looping thorough dict, setting each key as list to iterate over
    for year in dict_of_lists:
        year_list = dict_of_lists[year]
        holder = []
        
        ## Looping through each year pulling state generals
        for table in year_list:
            if len(table['Party'].unique()) > 1:
                tab_cols = list(table.columns)
                targ_cols = ['Party', 'Candidate', '%', 'Turnout', 'Total votes']
                slce_cols = []

                for c in tab_cols:
                    if c in targ_cols:
                        slce_cols.append(c)

                new_table = table[slce_cols].copy()
                holder.append(new_table)
     
        ## Try/except incase a year doesn't have that info
        ## Concats and stores final df into res_dict
        try:
            yr_df = pd.concat(holder, sort=False, ignore_index=True)
            res_dict[year] = yr_df
        except ValueError as e:
            print(f'{e}! Year {year}')
            res_dict[year] = holder
    
    return res_dict

def st_election_state_mapper(dict_of_dfs, lookup_ref):
    import pandas as pd
    import regex

    new_dict = {}

    ## Loop through keys i.e. years + container for cleaning
    for year in dict_of_dfs:
        #holder = []
        ## Loop through each election table + set col for incumbents
        if isinstance(dict_of_dfs[year], pd.DataFrame):
            table = dict_of_dfs[year]
            ## Covering up two '?' Candidates
            if year == '1932':
                table.at[124, 'Candidate'] = 'Unknown'
                table.at[125, 'Candidate'] = 'Unknown'
                table['Candidate'].fillna('Unknown', inplace=True)            
            
            try:
                table['Incumb_Y'] = 0
                table['State'] = None
                if 'Candidate' in table.columns:
                    table['Cln_name'] = table['Candidate'].map(lambda x: regex.sub(r'([A-z]{1,2}\.)\s?', '', x).strip())
                    table['Cln_name'] = table['Cln_name'].map(lambda x: regex.sub(r'\(([^\)]+)\)', '', x).strip())
                    table['Cln_name'] = table['Cln_name'].map(lambda x: regex.sub(r'\[([^\)]+)\]', '', x).strip())
                    ## Iterate over candidate's names 
                    for i, name in enumerate(table['Candidate']):
                        ## Check if incumbent + prep for state lookup
                        if '(Incumbent)' in name:
                            name = name.replace(' (Incumbent)', '')
                            table.at[i, 'Incumb_Y'] = 1

                        ## Helps to determine which are general elections + adding state
                        if name in list(lookup_ref['Incumbent']):
                            state = lookup_ref[lookup_ref['Incumbent'] == name].copy()
                            state_n = state['State_id'].values

                            ## Accounting for special elections
                            for st in state_n:
                                if not '(' in st:
                                    table.at[i, 'State'] = st

            except Exception as e:
                    print(f'Year:{year}, {e}, {e.args}')
                    display(table)
                    keep = input('Error with build, keep table? (Y/N):')
                    if keep is 'Y':
                        new_dict[year] = table
                        print(f'Table {year} saved!')
                    elif keep is 'N':
                        break
            
            if ('Turnout' in table.columns) & ('Total votes' in table.columns):
                table['Turnout'].update(table['Total votes'])
                table.drop(columns='Total votes', inplace=True)
                
            ## Storing each table for that year
            #holder.append(table)

            ## Storing year into dictionary
            new_dict[year] = table
        
    return new_dict

def sen_leader_collector(dict_of_lists):
    import pandas as pd

    res_dict = {}
    
    for year in dict_of_lists:
        try:
            table = dict_of_lists[year][0].copy()
            table.drop(index=0, inplace=True)
            res_dict[year] = table
        except KeyError as e:
            print(f'Error! {year}: {e}.')
            res_dict[year] = table
            continue
                
    return res_dict

def sen_leader_splitter(df, show=False):
    import pandas as pd 

    for col in df.iteritems():
        headers = col[1]
        
        for i, hdr in enumerate(headers):
            if isinstance(hdr, float):
                third_df = df.iloc[i:].copy()
                ldr_df = df.iloc[:i].copy()
                third_df.dropna(axis=1, how='all', inplace=True)
                third_df.dropna(axis=0, how='all', inplace=True)
                if show:
                    display(third_df)
                    display(ldr_df)
                    
                return ldr_df, third_df
        
        ldr_df = df.copy()
        third_df = None
        if show:
            display(ldr_df)
        
        return ldr_df, third_df

def sen_leader_cleaner(dict_of_dfs, show=False):
    import pandas as pd 
    
    res_dict = {}
    
    for year in dict_of_dfs:
        table = dict_of_dfs[year].copy()
        if show:
            display(table)
            
        ldr_df, third_df = sen_leader_splitter(table, show=show)
        
        if third_df is None:
            res_df = ldr_df.set_index(0, drop=True).copy()
            res_df = res_df.T
            res_df.reset_index(drop=True, inplace=True)
            if show:
                display(res_df)

            res_dict[year] = res_df

        else:
            ldr_df.set_index(0, drop=True, inplace=True)
            third_df.set_index(0, drop=True, inplace=True)
            res_df = ldr_df.merge(third_df, how='left', left_index=True, right_index=True).copy()
            res_df = res_df.T
            res_df.reset_index(drop=True, inplace=True)
            if show:
                display(res_df)            
            res_dict[year] = res_df
    
    return res_dict

def master_leader_tabler(dict_of_dfs):
    
    import pandas as pd
    
    holder1 = {}
    holder2 = []
    
    
    for year in dict_of_dfs:
        table = dict_of_dfs[year].copy()
        table['Year'] = year
        to_drop = table.columns.duplicated()
        table = table.loc[:, ~to_drop]
        holder1[year] = table
    
    lngest_yr = None
    len_cols = 1
    for year in holder1:
        table = holder1[year]
        t_len_cols = len(table.columns)

        if t_len_cols > len_cols:
            len_cols = t_len_cols
            lngest_yr = year
            print(f'Update! New col len {len_cols}.')
            print(f'Update! New year {lngest_yr}.')
            
    holder2.append(holder1[lngest_yr])
    
    for year in holder1:
        if year != lngest_yr:
            holder2.append(holder1[year])
        
    ldr_master_df = pd.concat(holder2, ignore_index=True, sort=True)
    ldr_master_df['Seats won'].update(ldr_master_df['Seats\xa0won'])
    ldr_master_df.drop(columns=['Seats\xa0won', 'Last\xa0election'], inplace=True)
    ldr_master_df.columns = ['Leader', 'Leaders_seat', 'Leader_since', 'Party', 'Percentage',
       'Popular_vote', 'Races_won', 'Seats_up', 'Seats_won', 'Seats_after',
       'Seats_before', 'Seat_change', 'Swing', 'Year']
    
    return ldr_master_df

def master_leader_cleaner(df, repl_dict=None, rd_stand=False, fillna_dict=None, fillna_stand=False, cols_to_slice=['Leader', 'Leaders_seat', 'Leader_since', 'Party', 'Seats_up', 'Seats_before', 'Year']):
    
    if isinstance(cols_to_slice, list):
        df_ = df[cols_to_slice].copy()
    else:
        df_ = df.copy()
        
    if isinstance(repl_dict, dict):
        repl_dict_ = repl_dict
        
    elif rd_stand:
        repl_dict_ = {'Seats_up':[(14, 0)],
                      'Leader_since':[(3, 'March 4, 1913'),(4, 'March 4, 1913'),
                                      (6, 'March 4, 1913'), (7, 'March 4, 1913'),
                                      (133, 'January 3, 2005'), (136, 'January 3, 2005'),
                                      (139, 'January 3, 2005'), (146, 'January 3, 2005'),
                                      (134, 'January 3, 2007'), (137, 'January 3, 2007'),
                                      (140, 'January 3, 2007'), (145, 'January 3, 2007')]}        
    else:
        print('No dictionary to replace values.')     
        
    try:
        for col in repl_dict_:
            to_repl = repl_dict_[col]
            
            for tup in to_repl:
                df_.at[tup[0], col] = tup[1]
    except:
        print('No values were replaced.')

    
    if isinstance(fillna_dict, dict):
        fillna_dict_ = fillna_dict
        
    elif fillna_stand:
        fillna_dict_ = {'Leader_since': {'method':'ffill', 'inplace':True},
                        'Leader': {'value':'3rd Party', 'inplace':True},
                        'Leaders_seat': {'value':'3rd Party', 'inplace':True}}
        
    else:
        print('No NAs to fill.')
        
    try:
        for col in fillna_dict_:
            to_fill = fillna_dict_[col]
            df_[col].fillna(**to_fill)
    except:
        print('No NAs were filled.')
        
    return df_

def regex_subber_bycol(df, col, pattern, replm='', multi_patt=False):
    import regex
    import pandas as pd
    
    ## Pattern for words in () & [] removal resp.
    ## r'\(([^\)]+)\)' ||| r'\[([^\)]+)\]'
    
    df_ = df.copy()
    
    if multi_patt:
        if isinstance(pattern, list):
            for patt in pattern:
                for idx, item in zip(df_.index, df_[col]):
                    if isinstance(item, str):
                        new_item = regex.sub(patt, replm, item)
                        df_.at[idx, col] = new_item
        else:
            print(('---'*10),'ERROR!', ('---'*10))
            print("Try adding [] to 'pattern' or setting 'multi_patt' to False.")
            return ''
    else:      
        for idx, item in zip(df_.index, df_[col]):
            if isinstance(item, str):
                new_item = regex.sub(pattern, replm, item)
                df_.at[idx, col] = new_item
        
    return df_

def yr_st_mapped_NA_handler(dict_of_dfs, turnout=True, candidate=True, percent=True, state=True):
    import pandas as pd
    import numpy as np
    res_dict = {}
    count = 0
    
    if turnout:
        t = 'Turnout'
        turn_patts = [r"'", r",", r'\[([^\)]+)\]']
        year_dict = {'1928':{36:1524914, 91:3026864},
                     '1930':{42:1207011},
                     '1932':{6:33980, 16:425634, 87:706440},
                     '1934':{98:308274},
                     '1936':{41:1803674},
                     '1942':{13:142342, 73:238487},
                     '1952':{34:2821133},
                     '1958':{59:616469},
                     '1974':{45:853521},
                     '1976':{102:514169},
                     '1980':{83:1098294},
                     '1986':{45:677105},
                     '1994':{20:356902},
                     '2000':{12:1311261, 61:944144, 80:3015662, 106:1928613, 113:6267964,
                             127:603477, 130:2540083},
                     '2002':{7:808256, 64:444542, 67:2112604},
                     '2004':{10:1039439, 24:1424726},
                     '2012':{19:693787, 34:2839572}}

        for year in dict_of_dfs:
            table = dict_of_dfs[year].copy()
            table['Year'] = year
            if year in year_dict:
                fill_vals = year_dict[year]
                table[t].fillna(value=fill_vals, inplace=True)
                table[t].fillna(method='ffill', inplace=True)
                table = regex_subber_bycol(table, t, turn_patts, multi_patt=True)
                table[t] = table[t].astype(np.int64)
                res_dict[year] = table
            elif (year == '1998') | (year == '2006'):
                table[t].dropna(axis=0, inplace=True)
                table[t] = table[t].astype(np.int64)
                res_dict[year] = table
            else:
                table = regex_subber_bycol(table, t, turn_patts, multi_patt=True)
                table[t] = table[t].astype(np.int64)
                res_dict[year] = table
                
        count += 1
    
    if candidate:
        c = 'Candidate'
        try:
            _ = res_dict['1932']
        except NameError:
            res_dict = dict_of_dfs.copy()
            
        table_2 = res_dict['1932'].copy()
        table_2.at[30, 'Candidate'] = 'Duncan U. Fletcher'
        table_2.at[30, '%'] = '100%'
        table_2.at[30, 'Incumb_Y'] = 1
        table_2.at[30, 'State'] = 'Florida'
        table_2.drop([31,32], axis=0, inplace=True)
        res_dict['1932'] = table_2
        
        count += 1
        
    if percent:
        p = '%'
        try:
            _ = res_dict['1932']
        except NameError:
            res_dict = dict_of_dfs.copy()
            
        perc_dict = {'1956':{68:'100'},
                     '2012':{25:'53.74', 26:'46.19', 52:'58.87', 53:'39.37', 54:'0.50'},
                     '2014':{91:'48.82', 92:'47.26', 93:'3.74', 94:'0.18'}}
        
        for year in res_dict:
            table_3 = res_dict[year].copy()
            if year in perc_dict:
                fill_vals = perc_dict[year]
                table_3[p].fillna(value=fill_vals, inplace=True)
                if year == '1956':
                    table_3.drop([69,70], axis=0, inplace=True)
                res_dict[year] = table_3
        
        count += 1
        
    if state:
        s = 'State'
        try:
            _ = res_dict['1994']
        except NameError:
            res_dict = dict_of_dfs.copy()
            
        for year in res_dict:
            table_4 = res_dict[year].copy()
            
            if year in ['1924', '1950', '1960', '1962', '1966']:
                table_4.at[0, s] = 'Alabama'
            elif year == '1992':
                table_4.at[0, s] = 'Alabama'
                table_4.at[0, 'Incumb_Y'] = 1
                table_4.at[1, s] = 'Alabama'
                table_4.at[2, s] = 'Alabama'
                table_4.at[3, s] = 'Alabama'
                table_4.at[127, s] = 'Wisconsin'
            elif year == '1968':
                table_4.at[96, s] = 'Washington'
                table_4.at[95, 'Party'] = 'Republican'
            elif year == '1980':
                table_4.at[66, 'Party'] = 'Republican'
                table_4.at[66, s] = 'New_York'
                table_4.at[73, s] = 'North_Carolina'
                table_4.at[74, 'Incumb_Y'] = 1
                table_4.at[74, 'Terms_in_office'] = 1
            elif year == '1986':
                table_4.at[24, s] = 'Connecticut'
                table_4.at[24, 'Candidate'] = 'Chris Dodd'
                table_4.at[24, 'Cln_name'] = 'Chris Dodd'
            elif year == '2006':
                table_4.at[7, s] = 'California'
                table_4.at[17, s] = 'Connecticut'
                table_4.at[23, s] = 'Delaware'


            table_4['State'].fillna(method='ffill', inplace=True)

            if year == '1992':
                table_4.drop([4,5,6,7,8,9], axis=0, inplace=True)
                table_4.reset_index(drop=True, inplace=True)
            elif year == '1968':
                table_4.drop([89,90,91,92,93,94], axis=0, inplace=True)
                table_4.reset_index(drop=True, inplace=True)
            elif year == '1986':
                table_4.drop([2,3,4,5,6,7,8], axis=0, inplace=True)
                table_4.reset_index(drop=True, inplace=True)
            elif year == '2006':
                table_4.drop([3,4,5,6,103,104,105,106,107], axis=0, inplace=True)
                table_4.reset_index(drop=True, inplace=True) 
            elif year == '2010':
                table_4.drop([2,3,4,5], axis=0, inplace=True)
                table_4.reset_index(drop=True, inplace=True)                
            
            res_dict[year] = table_4
        
        count += 1
        
    print(f'{count} NA operations completed.')
    return res_dict

def sen_leader_builder(df):
    import pandas as pd
    import numpy as np
    import regex
    
    try:
        new_df = df.copy()
    except:
        return 'Error in copying of DataFrame!'
    
    patterns = [r'\(([^\)]+)\)', r'\[([^\)]+)\]']
    new_df = regex_subber_bycol(new_df, 'Seats_before', patterns, multi_patt=True)
    #new_df = regex_subber_bycol(new_df, 'Seats_up', patterns, multi_patt=True)     

    new_df['Majority'] = 0
    new_df['Seats_up%'] = None
    new_df['Seats_before%'] = None
    new_df['Party_enc'] = None

    new_df['Seats_before'] = new_df['Seats_before'].astype(np.int64)
    new_df.at[new_df['Seats_before'].idxmax(), 'Majority'] = 1

    for idx, seats in zip(new_df.index, new_df['Seats_before']):
        total = new_df['Seats_before'].sum()
        new_df.at[idx, 'Seats_before%'] = (seats/total)

    new_df['Seats_up'] = new_df['Seats_up'].astype(np.int64)
    for idx, seats in zip(new_df.index, new_df['Seats_up']):
        if new_df['Seats_before'][idx] == 0:
            new_df.at[idx, 'Seats_up%'] = 0
        else:
            ins = seats / new_df['Seats_before'][idx]
            new_df.at[idx, 'Seats_up%'] = ins

    for idx, party in zip(new_df.index, new_df['Party']):
        if party == 'Republican':
            new_df.at[idx, 'Party_enc'] = 'R'
        elif party == 'Democratic':
            new_df.at[idx, 'Party_enc'] = 'D'
        elif party == 'Independent':
            new_df.at[idx, 'Party_enc'] = 'I'
        elif party == 'Socialist':
            new_df.at[idx, 'Party_enc'] = 'S'
        elif party == 'Socialist Labor':
            new_df.at[idx, 'Party_enc'] = 'S'
        elif party == 'Socialist Workers':
            new_df.at[idx, 'Party_enc'] = 'S'
        else:
            new_df.at[idx, 'Party_enc'] = 'T' 

    return new_df

def st_mapped_cleaner(dict_of_dfs, lookup_df, sen_ldr_df, genderize=False):
    import regex
    import pandas as pd
    import numpy as np
    from genderize import Genderize

    
    res_dict = {}
    count = 0
    
    for year in dict_of_dfs:
        count += 1
        table = dict_of_dfs[year].copy()
        lookup_table = lookup_df[lookup_df['Year'] == year].copy()
        sen_ldr_slce = sen_ldr_df[sen_ldr_df['Year'] == year].copy()
        
        table['Terms_in_office'] = 0
        table['Party_enc'] = None
        table['First_name'] = None
        if genderize:
            table['Gender'] = None
        
        ## REFORMATTING % AS A FLOAT    
        for i, p in zip(table.index, table['%']):
            if isinstance(p, str):
                if ',' in p:
                    p = p.replace(',', '.')
                if '<' in p:
                    p = p.replace('<', '')
                if '[23]' in p:
                    p = p.replace('[23]', '')
                if '%' in p:
                    try:
                        table.at[i, '%'] = np.float(p[:-1])
                    except ValueError as e:
                        print(year)
                        print(i)
                        

        ## REMOVING () & [] FROM THE NAMES
        patterns = [r'\(([^\)]+)\)', r'\[([^\)]+)\]']
        table = regex_subber_bycol(table, 'Candidate', patterns, multi_patt=True)

        # if year == '1932':
        #     res_dict[year] = table
        #     continue
        
        ## M
        for n_idx, name in zip(table.index, table['Cln_name']):
            for i_idx, incmb in zip(lookup_table.index, lookup_table['Cln_name']):
                if incmb == name:
                    table.at[n_idx, 'Terms_in_office'] = lookup_table['Terms_in_office'][i_idx]

                    if table['Incumb_Y'][n_idx] != 1:
                        table.at[n_idx, 'Incumb_Y'] = 1  

                    if table['Party'][n_idx] != lookup_table['Party'][i_idx]:
                        table.at[n_idx, 'Party'] = lookup_table['Party'][i_idx]         
        
        ## MK
        for idx, party in zip(table.index, table['Party']):
            if party == 'Republican':
                table.at[idx, 'Party_enc'] = 'R'
            elif party == 'Democratic':
                table.at[idx, 'Party_enc'] = 'D'
            elif party == 'Independent':
                table.at[idx, 'Party_enc'] = 'I'
            elif party == 'Socialist':
                table.at[idx, 'Party_enc'] = 'S'
            elif party == 'Socialist Labor':
                table.at[idx, 'Party_enc'] = 'S'
            elif party == 'Socialist Workers':
                table.at[idx, 'Party_enc'] = 'S'
            else:
                table.at[idx, 'Party_enc'] = 'T'              

        ## OI
        for idx, name in zip(table.index, table['Cln_name']):
            first = regex.findall(r'([A-Z]{1}[A-z]+\s{1})', name)
            try:
                first = first.pop()
                first = first.strip()
                table.at[idx, 'First_name'] = first
            except IndexError:
                table.at[idx, 'First_name'] = name
                
        ## TY
        if genderize:
            genderizer = Genderize()
            
            for idx, name in zip(table.index, table['First_name']):
                pred = None
                guess = genderizer.get([name])[0]

                if guess['gender'] == 'male':
                    if guess['probability'] < .60:
                        pred = 'F'
                    else:
                        pred = 'M'

                if guess['gender'] == 'female':
                    if guess['probability'] < .60:
                        pred = 'M'
                    else:
                        pred = 'F'

                table.at[idx, 'Gender'] = pred
        
        ## DF
        try:
            sen_ldr_slce = sen_leader_builder(sen_ldr_slce)
            
            to_map1 = sen_ldr_slce.set_index('Party_enc')['Seats_up%']
            if to_map1.shape[0] > 2:
                to_map1 = to_map1.groupby(level=0).sum()

            table['Seats_up%'] = table['Party_enc'].map(to_map1)
            table['Seats_up%'].fillna(0, inplace=True)

            to_map2 = sen_ldr_slce.set_index('Party_enc')['Seats_before%']
            if to_map2.shape[0] > 2:
                to_map2 = to_map2.groupby(level=0).sum()
                
            table['Seats_before%'] = table['Party_enc'].map(to_map2)
            table['Seats_before%'].fillna(0, inplace=True)
        except KeyError as e:
            display(table)
            print(e)
            break
        
        table.drop(columns=['Party', 'Candidate'], inplace=True)
        res_dict[year] = table
        
        if count%20 == 0:
            print(f'20 loops done! Just finished {year}.')

    print(f'Finished {count} years! Latest year collected {year}.')    
    return res_dict

def cln_st_combiner(dict_of_dfs):
    import pandas as pd
    
    holder = []
    
    for year in dict_of_dfs:
        table = dict_of_dfs[year].copy()
        holder.append(table)
        
    df = pd.concat(holder, ignore_index=True)
    
    return df

class Timer():
    
    """Timer class designed to keep track of and save modeling runtimes. It
    will automatically find your local timezone. Methods are .stop, .start,
    .record, and .now"""
    
    def __init__(self, fmt="%m/%d/%Y - %I:%M %p", verbose=None):
        import tzlocal
        self.verbose = verbose
        self.tz = tzlocal.get_localzone()
        self.fmt = fmt
        
    def now(self):
        import datetime as dt
        return dt.datetime.now(self.tz)
    
    def start(self, disp_time=True):
        if disp_time:
            print(f'---- Timer started at: {self.now().strftime(self.fmt)} ----')
        self.started = self.now()
        
    def stop(self, disp_time=True):
        if disp_time:
            print(f'---- Timer stopped at: {self.now().strftime(self.fmt)} ----')
        self.stopped = self.now()
        self.time_elasped = (self.stopped - self.started)
        if disp_time:
            print(f'---- Time elasped: {self.time_elasped} ----')
        
    def record(self):
        try:
            self.lap = self.time_elasped
            return self.lap
        except:
            return print('---- Timer has not been stopped yet... ----')
        
    def __repr__(self):
        return f'---- Timer object: TZ = {self.tz} ----'

def fit_n_pred(reg_, X_tr, X_te, y_tr, show_reg=True):
    
    """Takes in Classifier, training data (X,y), and test data(X). Will output 
    predictions based upon both the training and test data using the sklearn
    .predict method. MUST unpack into two variables (train, test)."""

    try:
        timer = Timer()
        timer.start(disp_time=False)
    except:
        print('No timer for fitting.')
    
    reg_.fit(X_tr, y_tr)

    y_hat_trn = reg_.predict(X_tr)
    y_hat_tes = reg_.predict(X_te)

    try:
        timer.stop(disp_time=False)
    except:
        pass
    
    if show_reg:
        display(reg_)
    return y_hat_trn, y_hat_tes

def grid_searcher(reg_, params, X_tr, X_te, y_tr, y_te, cv=None, keep_t=False, custom_scorer=None, train_score=True):
    
    """Takes any classifier, train/test data for X/y, and dict of parameters to
    iterate over. Optional parameters select for cross-validation tuning, keeping
    time for running the gridsearch, and returning training scores when done.
    Default parameters only return the fitted grid search object. MUST HAVE Timer
    class imported."""
    
    from sklearn.model_selection import GridSearchCV
    import numpy as np
    
    ## Instantiate obj. with our targets
    grid_s = GridSearchCV(reg_, params, cv=cv, scoring=custom_scorer, return_train_score=train_score)
    
    ## Time and fit run the 'search'
    time = Timer()
    time.start()
    grid_s.fit(X_tr, y_tr)
    time.stop()
    
    ## Display results
    tr_score = np.mean(grid_s.cv_results_['mean_train_score'])
    te_score = grid_s.score(X_te, y_te)
    print(f'Mean Training Score: {tr_score :.2%}')
    print(f'Mean Test Score: {te_score :.2%}')
    print('Best Parameters:')
    print(grid_s.best_params_)
    
    ## Time keeping and grid obj
    if keep_t:
        lap = time.record().total_seconds()
        print('**********All done!**********')
        return grid_s, lap
    else:
        return grid_s