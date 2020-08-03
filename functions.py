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

    ## Dataframe with Sentors as index + states as values
    state_ref_df = pd.DataFrame({'State_id':st_list, 'Incumbent':sntr_list})
    #state_ref_df.columns = ['State_id']
    
    ## Modifying list of states to that of the ref table OR not + return
    if mod_df:
        summary_df['State'] = st_list
        return summary_df, state_ref_df
    else:
        return state_ref_df

def master_tabler(yr_summary_dict):
    import pandas as pd

    holder = []

    for year in yr_summary_dict:
        holder.append(yr_summary_dict[year][1])

    name_lookup_df = pd.concat(holder, ignore_index=True)
    
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
                targ_cols = ['Party', 'Candidate', '%', 'Turnout']
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

    new_dict = {}

    ## Loop through keys i.e. years + container for cleaning
    for year in dict_of_dfs:
        #holder = []
        ## Loop through each election table + set col for incumbents
        if isinstance(dict_of_dfs[year], pd.DataFrame):
            table = dict_of_dfs[year]
            
            try:
                table['Incumb_Y'] = 0
                table['State'] = None
                if 'Candidate' in table.columns:
                    ## Iterate over candidate's names 
                    for i, name in enumerate(table['Candidate']):
                        ## Check if incumbent + prep for state lookup
                        if '(Incumbent)' in name:
                            name = name.replace(' (Incumbent)', '')
                            table['Incumb_Y'].iloc[i] = 1

                        ## Helps to determine which are general elections + adding state
                        if name in list(lookup_ref['Incumbent']):
                            state = lookup_ref[lookup_ref['Incumbent'] == name].copy()
                            state_n = state['State_id'].values

                            ## Accounting for special elections
                            for st in state_n:
                                if not '(' in st:
                                    table['State'][i] = st

            except Exception as e:
                    print(f'Year:{year}, {e}, {e.args}')
                    display(table)
                    keep = input('Error with build, keep table? (Y/N):')
                    if keep is 'Y':
                        new_dict[year] = table
                        print(f'Table {year} saved!')
                    elif keep is 'N':
                        break

            ## Storing each table for that year
            #holder.append(table)

            ## Storing year into dictionary
            new_dict[year] = table
        
    return new_dict

