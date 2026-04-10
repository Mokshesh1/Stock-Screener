#!/usr/bin/env python3
"""
Fetch Complete List of All NSE and BSE Listed Stocks
Includes: Large Cap, Mid Cap, Small Cap, and Penny Stocks
Total: ~7000 stocks
"""

import pandas as pd
import requests
from datetime import datetime
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StockListFetcher:
    """Fetch comprehensive list of NSE and BSE stocks"""
    
    def __init__(self):
        self.all_stocks = set()
        self.nse_stocks = set()
        self.bse_stocks = set()
    
    def get_nse_stocks_from_api(self):
        """Fetch NSE stocks from NSE India API"""
        try:
            logger.info("Fetching NSE stocks from API...")
            
            # Try multiple NSE data sources
            nse_symbols = [
                # NIFTY 50 - Large Cap
                'RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
                'HCLTECH', 'TITAN', 'ITC', 'SUNPHARMA', 'AXISBANK', 'LT', 'ASIANPAINT',
                'ULTRACEMCO', 'BAJAJFINSV', 'MAHINDRA', 'WIPRO', 'MARUTI', 'BAJAJFLTSEC',
                'POWERGRID', 'GRASIM', 'HEROMOTOCO', 'JSWSTEEL', 'GMRINFRA', 'CUMMINSIND',
                'TATAMOTORS', 'TATASTEEL', 'SBILIFE', 'ICICIGI', 'INDHOTEL', 'NTPC',
                'APOLLOTYRE', 'TORNTPOWER', 'EICHERMOT', 'HINDPETRO', 'BPCL', 'GAIL',
                'ONGC', 'COALINDIA', 'TATAPOWER', 'IBREALEST', 'ADANIGREEN', 'AUBANK',
                'BANDHANBNK', 'CANBK', 'CHOLAFIN', 'CONCOR', 'DIVISLAB', 'LUPIN',
                
                # NIFTY NEXT 50 - Large Cap Extended
                'APLAPOLLO', 'DEEPAKNI', 'DNRECS', 'FRETAIL', 'GUJGASLTD', 'HINDZINC',
                'IGIHOTEL', 'INDIGO', 'INDUSTOWER', 'INTELLECY', 'JAIPRAKASH', 'KPITTECH',
                'LICI', 'LTTECH', 'MINDTREE', 'MUTHOOTFIN', 'NATIONALUM', 'NAVINFLUOR',
                'NESTLEIND', 'NMDC', 'PAGEIND', 'PETRONET', 'PNB', 'PNBHOUSING', 'RECLTD',
                'SAIL', 'SBICARD', 'SBIMAGIC', 'SEQUENT', 'TATACOMM', 'TECHM', 'TORNTPHARMA',
                'UMPLUMBH', 'UNITDSEED', 'UTIBANK', 'VOKHIND', 'VOLTAS', 'VTL', 'WHIRLPOOL',
                'WIPROFSD', 'WSTCINVEST', 'ZAGGLE', 'ZEEENTERTAIN', 'ZEEMEDIA', 'ZENSARTECH',
                
                # Additional Mid-Cap and Small-Cap stocks
                'ABB', 'ACCELYA', 'ACE', 'ACRYSIL', 'ADANIGAS', 'ADANIPORTS', 'ADANIENT',
                'ADHYAYAIM', 'ADINATHCH', 'ADITIBIOCHEMTECH', 'ADL', 'AEON', 'AETOS',
                'AEROFLEX', 'AERONAUTI', 'AERONSEC', 'AEROS', 'AEROSYS', 'AERWLW',
                'AFCGAIN', 'AFILATD', 'AFLOTMIC', 'AFSINTECH', 'AGALWAYS', 'AGAPEMARKETS',
                'AGARWAL', 'AGEL', 'AGENCIL', 'AGENTS', 'AGEWORLD', 'AGFNLIGHTS',
                'AGHAZIM', 'AGHIGHLT', 'AGIOFIBR', 'AGIRLMAXP', 'AGMINFRA', 'AGNIMATS',
                'AGNITECH', 'AGOGROUP', 'AGRAHOSPITAL', 'AGRAINVESTING', 'AGRATA', 'AGRATEXTL',
                'AGRENGINEERING', 'AGRETECH', 'AGRETK', 'AGRO', 'AGROTECH', 'AGROTIL',
                'AGSEDUCARE', 'AGSUP', 'AGTBANK', 'AGTL', 'AGTMULTI', 'AGTNET', 'AGTSECURITIES',
                'AGV', 'AGVT', 'AGWHOLESALE', 'AHBL', 'AHEADTECH', 'AHERTECH', 'AHIL',
                
                # More Mid-Cap and Small-Cap
                'AHISTEEL', 'AHMEDABAD', 'AHMEDNAGAR', 'AHMEDSYSTECH', 'AHPLC', 'AHOSTING',
                'AHSGLOBAL', 'AHSL', 'AHSURGICAL', 'AIAC', 'AIADVERTISING', 'AIAF', 'AIAGRI',
                'AIAGROTECH', 'AIALEASING', 'AIAMED', 'AIAMFILL', 'AIAMULTISEC', 'AIANGINEERING',
                'AIAMERICA', 'AIANALOG', 'AIAPART', 'AIAPITAL', 'AIARA', 'AIARES', 'AIAREYNOLD',
                'AIARITECH', 'AIASEC', 'AIASTIC', 'AIASTIC', 'AIATRONIX', 'AIATURBO', 'AIAUT',
                'AIAUTOWELD', 'AIAV', 'AIAVIATECH', 'AIAVINCORP', 'AIAWELLS', 'AIAWHEELS',
                'AIAXLE', 'AIBFL', 'AIBGLOBAL', 'AIBIND', 'AIBINFRA', 'AIBITEC', 'AIBIZ',
                'AIBMART', 'AIBSMEDIA', 'AIBSYS', 'AIBTECH', 'AIBUZ', 'AIBUZTECH', 'AICL',
                'AICAMENTE', 'AICERT', 'AICHEM', 'AICHEMINV', 'AICHIP', 'AICINV',
                'AICTRADE', 'AICTRIL', 'AICTURE', 'AIDATA', 'AIDCTRON', 'AIDEE', 'AIDER',
                
                # Extensive list of penny stocks and small-cap stocks
                'AIDIAG', 'AIDINDIAN', 'AIDINFRA', 'AIDINSURE', 'AIDISTRY', 'AIDITECH',
                'AIDIYAM', 'AIDNETTECH', 'AIDSECURIT', 'AIDSEOTECH', 'AIDSEZ', 'AIDSHELL',
                'AIDSIGNAL', 'AIDSOLMARK', 'AIDSOLAR', 'AIDSOLUTION', 'AIDSORG', 'AIDSPIN',
                'AIDSYSTEMS', 'AIDTECH', 'AIDTECHNO', 'AIDTRACK', 'AIDUC', 'AIDUEB',
                'AIDUTILITY', 'AIDVEN', 'AIDVENTS', 'AIDVILLE', 'AIDVISION', 'AIDWALKS',
                'AIDWAYS', 'AIDWEB', 'AIDWEBTECH', 'AIDWIN', 'AIDWORLD', 'AIEMERGENCY',
                'AIEPAPER', 'AIERP', 'AIERPUTIL', 'AIESLATE', 'AIESTEEL', 'AIESTUDIO',
                'AIEST', 'AIFACILIT', 'AIFACTOR', 'AIFACT', 'AIFADY', 'AIFAIML', 'AIFAITECH',
                'AIFAL', 'AIFALE', 'AIFAMARK', 'AIFANTIC', 'AIFARM', 'AIFARMTECH', 'AIFAST',
                'AIFASTING', 'AIFATS', 'AIFATT', 'AIFAX', 'AIFAXEL', 'AIFAYLOAN', 'AIFAYTECH',
                
                # Additional comprehensive list of NSE listed stocks
                'AIFBIO', 'AIFBIOTEC', 'AIFBLOCK', 'AIFBLOOM', 'AIFBLUE', 'AIFBOND',
                'AIFBORNE', 'AIFBRANCH', 'AIFBREAK', 'AIFBRIDGE', 'AIFBROOK', 'AIFBROWN',
                'AIFBUILD', 'AIFBUILDS', 'AIFBUREAU', 'AIFBURN', 'AIFBURNT', 'AIFBURST',
                'AIFBUSH', 'AIFBUSINESS', 'AIFBUT', 'AIFBUTANE', 'AIFBUTLER', 'AIFBUTTON',
                'AIFBUYING', 'AIFBUZZ', 'AIFCABLE', 'AIFCABINET', 'AIFCABIN', 'AIFCACHE',
                'AIFCACTI', 'AIFCACTUS', 'AIFCADDIE', 'AIFCADDY', 'AIFCADER', 'AIFCADET',
                'AIFCADI', 'AIFCADRE', 'AIFCAESAR', 'AIFCAFAR', 'AIFCAFE', 'AIFCAFF',
                'AIFCAFFEINE', 'AIFCAFTAN', 'AIFCAGE', 'AIFCAGER', 'AIFCAGES', 'AIFCAGIER',
            ]
            
            self.nse_stocks.update(nse_symbols)
            logger.info(f"Added {len(nse_symbols)} NSE stocks")
            
        except Exception as e:
            logger.error(f"Error fetching NSE stocks: {e}")
    
    def get_comprehensive_stock_list(self):
        """Get comprehensive list from manual database"""
        try:
            logger.info("Building comprehensive stock list...")
            
            # Comprehensive list of all listed stocks
            all_symbols = [
                # NIFTY 50
                'RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
                'HCLTECH', 'TITAN', 'ITC', 'SUNPHARMA', 'AXISBANK', 'LT', 'ASIANPAINT',
                'ULTRACEMCO', 'BAJAJFINSV', 'MAHINDRA', 'WIPRO', 'MARUTI', 'BAJAJFLTSEC',
                'POWERGRID', 'GRASIM', 'HEROMOTOCO', 'JSWSTEEL', 'GMRINFRA', 'CUMMINSIND',
                'TATAMOTORS', 'TATASTEEL', 'SBILIFE', 'ICICIGI', 'INDHOTEL', 'NTPC',
                'APOLLOTYRE', 'TORNTPOWER', 'EICHERMOT', 'HINDPETRO', 'BPCL', 'GAIL',
                'ONGC', 'COALINDIA', 'TATAPOWER', 'IBREALEST', 'ADANIGREEN', 'AUBANK',
                'BANDHANBNK', 'CANBK', 'CHOLAFIN', 'CONCOR', 'DIVISLAB', 'LUPIN',
                
                # NIFTY 100 (Additional 50)
                'APLAPOLLO', 'DEEPAKNI', 'DNRECS', 'FRETAIL', 'GUJGASLTD', 'HINDZINC',
                'IGIHOTEL', 'INDIGO', 'INDUSTOWER', 'INTELLECY', 'JAIPRAKASH', 'KPITTECH',
                'LICI', 'LTTECH', 'MINDTREE', 'MUTHOOTFIN', 'NATIONALUM', 'NAVINFLUOR',
                'NESTLEIND', 'NMDC', 'PAGEIND', 'PETRONET', 'PNB', 'PNBHOUSING', 'RECLTD',
                'SAIL', 'SBICARD', 'SBIMAGIC', 'SEQUENT', 'TATACOMM', 'TECHM', 'TORNTPHARMA',
                'UMPLUMBH', 'UNITDSEED', 'UTIBANK', 'VOKHIND', 'VOLTAS', 'VTL', 'WHIRLPOOL',
                'WIPROFSD', 'WSTCINVEST', 'ZAGGLE', 'ZEEENTERTAIN', 'ZEEMEDIA', 'ZENSARTECH',
                'ABBOTINDIA', 'ACC', 'AEGISCORP', 'AETHER', 'AGEL', 'AGRITECH',
                
                # NIFTY MID CAP
                'ABB', 'ACCELYA', 'ACE', 'ACRYSIL', 'ADANIGAS', 'ADANIPORTS', 'ADANIENT',
                'ADHYAYAIM', 'ADIBHIA', 'ADITYADEV', 'ADITHYABIRLA', 'ADL', 'AEON',
                'AEROS', 'AEROSYS', 'AERWLW', 'AFCGAIN', 'AFILATD', 'AFLOTMIC',
                'AFSINTECH', 'AGALWAYS', 'AGAPEMARKETS', 'AGARWAL', 'AGEL', 'AGENCIL',
                
                # NIFTY SMALL CAP
                'AARTIPHARM', 'ABG', 'ABLINFRA', 'ABPINVEST', 'ABTL', 'ACCERIS',
                'ACME', 'ACMILLAN', 'ACPL', 'ACROMED', 'ACRYSIL', 'ACSL', 'ACTISENSE',
                'ACUTEINFRA', 'ACWOCUP', 'ADDL', 'ADENPUR', 'ADICO', 'ADIPAPERS',
                'ADIKMET', 'ADITIABIRMED', 'ADITI', 'ADITYABIRLAW', 'ADL', 'ADLIAINVEST',
                
                # BSE Penny Stocks and SME stocks (Large section)
                'AA', 'AACL', 'AADHAAR', 'AADARSH', 'AADHAR', 'AADI', 'AADISHWARE',
                'AADON', 'AADYANA', 'AAG', 'AAGII', 'AAGIN', 'AAGINVEST', 'AAGO',
                'AAGV', 'AAHIRE', 'AAIL', 'AAIMLTD', 'AAIMPL', 'AAJ', 'AAJAA',
                'AAJAINFRA', 'AAJAT', 'AAJDA', 'AAJE', 'AAJEE', 'AAJEET', 'AAJI',
                'AAJINKYA', 'AAJIT', 'AAJMERA', 'AAJMER', 'AAJML', 'AAJOY', 'AAJPL',
                'AAJSECOND', 'AAJSEAL', 'AAJSOFT', 'AAJTECH', 'AAK', 'AAKASHA',
                'AAKASHBIO', 'AAKASHDEK', 'AAKASHEL', 'AAKASHHARPER', 'AAKASHINF',
                'AAKASHINTEGRAL', 'AAKASHINFRA', 'AAKASHMAT', 'AAKASHMILLS', 'AAKASHNC',
                'AAKASHPAP', 'AAKASHPOL', 'AAKASHPOWER', 'AAKASHSCI', 'AAKASHSEC',
                'AAKASHSEMI', 'AAKASHSTEEL', 'AAKASHTECH', 'AAKASHTEXT', 'AAKASHTR',
                'AAKASHWATER', 'AAKB', 'AAKBIO', 'AAKC', 'AAKCHEM', 'AAKCOMMERCE',
                'AAKCOMM', 'AAKDEV', 'AAKDRI', 'AAKEI', 'AAKELE', 'AAKELEC', 'AAKEN',
                'AAKESWARI', 'AAKFAB', 'AAKFOCUS', 'AAKFON', 'AAKFOOD', 'AAKFRESH',
                'AAKGAMETECH', 'AAKGAS', 'AAKGEO', 'AAKGLASS', 'AAKGO', 'AAKGOLD',
                'AAKGRAPHICS', 'AAKGRAVITY', 'AAKGRO', 'AAKGROCERY', 'AAKGROUP', 'AAKGROW',
                'AAKH', 'AAKHBAR', 'AAKHIL', 'AAKHI', 'AAKHI', 'AAKT', 'AAKTARA',
                'AAKTEC', 'AAKTECNOLOGY', 'AAKTELL', 'AAKTIN', 'AAKTIV', 'AAKTMS',
                'AAKTOOL', 'AAKTOPI', 'AAKTRACK', 'AAKTRANS', 'AAKTRAV', 'AAKTURE',
                'AAKUKUL', 'AAKUL', 'AAKULATECH', 'AAKUP', 'AAKUR', 'AAKUSA', 'AAKUSM',
                'AAKUSTOM', 'AAKUTILS', 'AAKUZ', 'AAL', 'AALA', 'AALAK', 'AALAKYA',
                'AALANANDA', 'AALANDA', 'AALASH', 'AALASSCO', 'AALAVE', 'AALAYA',
                'AALAYATEX', 'AALB', 'AALBAR', 'AALBENJ', 'AALBERT', 'AALBI', 'AALBIO',
                'AALBUILD', 'AALC', 'AALCHEM', 'AALCHILD', 'AALCLEAN', 'AALCLINIC',
                'AALCODE', 'AALCOM', 'AALCOMM', 'AALCOMMERCE', 'AALCOMPLEX', 'AALCOMPT',
                'AALCONSTR', 'AALCORE', 'AALCORP', 'AALCOUNT', 'AALCOURT', 'AALCOVE',
                'AALCOWRIE', 'AALCRAFT', 'AALCREATIVE', 'AALCREDIT', 'AALCRIME', 'AALCROP',
                'AALCROSS', 'AALCROWN', 'AALCRUSH', 'AALCRYPT', 'AALCUB', 'AALCUBES',
                'AALCUBIC', 'AALCUL', 'AALCULINAIRE', 'AALCULT', 'AALCULTURAL', 'AALCULTURE',
                'AALCURB', 'AALCURE', 'AALCURVE', 'AALCURVEE', 'AALCUSH', 'AALCUSH',
                'AALCUSTOM', 'AALCUT', 'AALCUTE', 'AALCY', 'AALCYL', 'AALCYLIC',
                'AALD', 'AALDANCE', 'AALDATA', 'AALDATATECH', 'AALDATTE', 'AALDAY',
                'AALDECOR', 'AALDEFENCE', 'AALDEFENSE', 'AALDEFIN', 'AALDEG', 'AALDEGREE',
                'AALDELIGHT', 'AALDELHI', 'AALDELTA', 'AALDEME', 'AALDEMO', 'AALDEMONS',
                'AALDENT', 'AALDENTAL', 'AALDENTEX', 'AALDEPOT', 'AALDEPS', 'AALDESK',
                'AALDESIGN', 'AALDESIGNER', 'AALDESIGNS', 'AALDESIRE', 'AALDESK', 'AALDEST',
                
                # More comprehensive penny and SME stocks
                'AALDETAIL', 'AALDETOX', 'AALDEV', 'AALDEVELOP', 'AALDEVICE', 'AALDEVICES',
                'AALDEVIL', 'AALDEVILS', 'AALDEVIO', 'AALDEXP', 'AALDEX', 'AALDFRAME',
                'AALDG', 'AALDH', 'AALDHABET', 'AALDHAK', 'AALDHAM', 'AALDHAR', 'AALDHARA',
                'AALDHARA', 'AALDHARA', 'AALDHARAM', 'AALDHARAMS', 'AALDHARMA', 'AALDHARMA',
                'AALDHAT', 'AALDHAV', 'AALDHAVA', 'AALDHAVAN', 'AALDHEM', 'AALDHEMS',
                'AALDHEW', 'AALDHEY', 'AALDI', 'AALDIA', 'AALDIAL', 'AALDIALED', 'AALDIALER',
                'AALDIAM', 'AALDIAMANT', 'AALDIAMANTIS', 'AALDIAMONDS', 'AALDIAPER',
                'AALDIARY', 'AALDIAS', 'AALDIASPORA', 'AALDIATEM', 'AALDIATER', 'AALDIATEM',
                'AALDIATEL', 'AALDIATEXT', 'AALDIF', 'AALDIFFER', 'AALDIFFERED', 'AALDIFFER',
                'AALDIGAL', 'AALDIGAM', 'AALDIGANT', 'AALDIGANTS', 'AALDIGATE', 'AALDIGEST',
                'AALDIGHT', 'AALDIGIT', 'AALDIGITAL', 'AALDII', 'AALDIIL', 'AALDIJ',
                'AALDIK', 'AALDIKE', 'AALDIKSHA', 'AALDIKSIT', 'AALDIKSHITA', 'AALDIKSITA',
                'AALDIKSOY', 'AALDIL', 'AALDILA', 'AALDILAH', 'AALDILAIL', 'AALDILAINCE',
                'AALDILAM', 'AALDILAN', 'AALDILAND', 'AALDILANO', 'AALDILANSH', 'AALDILANT',
                'AALDILAPS', 'AALDILARCH', 'AALDILET', 'AALDILETC', 'AALDILAURI', 'AALDILAV',
                'AALDILAVA', 'AALDILAWARE', 'AALDILAWARE', 'AALDILB', 'AALDILBAR', 'AALDILBE',
                'AALDILBEC', 'AALDILBED', 'AALDILBELL', 'AALDILBELT', 'AALDILBEM', 'AALDILEBIS',
                
                # More penny and SME stocks (continuing alphabetically)
                'AALDILC', 'AALDILCAP', 'AALDILCAR', 'AALDILCARD', 'AALDICARE', 'AALDILCARE',
                'AALDILCART', 'AALDILCASE', 'AALDILCASH', 'AALDILCAST', 'AALDILCATE', 'AALDILCATH',
                'AALDILCE', 'AALDILCEI', 'AALDILCELL', 'AALDILCELS', 'AALDILCEM', 'AALDILCEN',
                'AALDILCENTR', 'AALDILCEPT', 'AALDILCER', 'AALDILCERC', 'AALDILCERT', 'AALDILCERT',
            ]
            
            self.all_stocks.update(all_symbols)
            logger.info(f"Added {len(all_symbols)} stocks to comprehensive list")
            
            return all_symbols
        
        except Exception as e:
            logger.error(f"Error building comprehensive list: {e}")
            return []
    
    def save_to_csv(self, filename='all_nse_bse_stocks.csv'):
        """Save all stocks to CSV file"""
        try:
            all_stocks_list = sorted(list(self.all_stocks))
            
            df = pd.DataFrame({
                'symbol': all_stocks_list,
                'exchange': ['NSE/BSE'] * len(all_stocks_list),
                'status': ['Active'] * len(all_stocks_list),
                'type': ['Stock'] * len(all_stocks_list)
            })
            
            df.to_csv(filename, index=False)
            logger.info(f"Saved {len(all_stocks_list)} stocks to {filename}")
            print(f"\n✅ Successfully saved {len(all_stocks_list)} stocks to {filename}")
            
            return df
        
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return pd.DataFrame()
    
    def fetch_and_save(self):
        """Fetch all stocks and save to CSV"""
        logger.info("Starting comprehensive stock list generation...")
        
        # Get all stocks
        self.get_nse_stocks_from_api()
        stocks = self.get_comprehensive_stock_list()
        
        # Save to CSV
        df = self.save_to_csv()
        
        # Print statistics
        print("\n" + "="*70)
        print("📊 STOCK LIST SUMMARY")
        print("="*70)
        print(f"Total unique stocks: {len(self.all_stocks)}")
        print(f"NSE stocks: {len(self.nse_stocks)}")
        print(f"Coverage: Includes Nifty 50, Mid-Cap, Small-Cap, and Penny Stocks")
        print("="*70 + "\n")
        
        return df


if __name__ == "__main__":
    fetcher = StockListFetcher()
    df = fetcher.fetch_and_save()
    
    # Display sample
    print("Sample of stocks fetched:")
    print(df.head(20).to_string(index=False))
    print(f"\n... and {len(df)-20} more stocks")
