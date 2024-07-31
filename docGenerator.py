from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm
from pathlib import Path

# import sys, os, inspect
# SCRIPT_DIR = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
# sys.path.append(os.path.dirname(SCRIPT_DIR))

ABS_PATH = Path(__file__).parent

def transform_date(date):

    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
           'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    year,month,day = date.split('-')
    return f'«{day}» {months[int(month) - 1]} {year}'
   
def vibraTable_DocGenerator(name,
                            a,
                            b,
                            h,
                            m,
                            heights,
                            test_date,
                            loads,
                            protocol,
                            results,
                            savedir):

    template = ABS_PATH / 'VibraTable_Template.docx'
    doc = DocxTemplate(template)
    context = {
        'name':name,
        'test_date': transform_date(test_date),
        'a':a,
        'b':b,
        'h':h,
        'loads':loads,
        'tbl_contents': [], # добавляется позже, через цикл
        'pic_contents': [],
    }

    for M in loads:
        try:
            context['tbl_contents'].append(
                {'load':M, 
                 'pressure':f'{(M/a/b * 9.81 *1e3):.2f}', 
                 'Fpeak':f'{results[M][0]:.2f}', 
                 'Ed':f'{results[M][1]:.2f}', 
                 'damp':f'{results[M][2]:.2f}'}
                )
        except KeyError:
            context['tbl_contents'].append(
                {'load':M, 
                 'pressure':f'{(M/a/b * 9.81 *1e-3):.2f}', 
                 'Fpeak':'-', 
                 'Ed':'-', 
                 'damp':'-'}
                )
        context['pic_contents'].append(
            {
                'pic':InlineImage(doc, savedir + f'/{name}_{str(M)}кг.png', width=Cm(14)),  #, height=Cm(10)
                'load':M,
                }
            )
        
    rez_file = Path(savedir + f'/{name}_rez.png')
    if rez_file.is_file():
        context['rez_pic'] = InlineImage(doc, savedir + f'/{name}_rez.png', width=Cm(16))
    else:
        context['rez_pic'] = False
        
    while True:
        for var in loads:
            if var not in [2.0, 5.0, 10.0]:
                display_paragraph = False
                break
        bad_loads = [var for var in [2.0, 5.0, 10.0] if var not in loads]
        if len(bad_loads) > 0:
            display_paragraph = True                
            break
        display_paragraph = False
        break
        
    context['bad_loads'] = bad_loads
    context['display_paragraph'] = display_paragraph
    if m != None:
        context['m'] = m
    if protocol != None:
        context['protocol'] = protocol

    
    doc.render(context=context)
    if protocol != None:
        doc.save(f'{savedir}/ДС-003-{test_date[:4]}-В{protocol}.docx')
    else:
        doc.save(f'{savedir}/ДС-003-{test_date[:4]}-В_{name}.docx')


def statica_DocGenerator(name,
                         a,
                         b,
                         h,
                         m,
                         test_date,
                         protocol,
                         results,
                         savedir,
                         ):

    template = ABS_PATH / 'Statica_Template.docx'
    doc = DocxTemplate(template)
    context = {
        'name':name,
        'test_date': transform_date(test_date),
        'a' : a,
        'b' : b,
        'h' : h,
        'relax' : f"{results['relax']:.2f}",
        'relax_t' : f"{results['relax_t']:.2f}",
        'load_pic' : InlineImage(doc, savedir + f'/{name}_нагрузка.png', width=Cm(22)),
        'cycles_pic' : InlineImage(doc, savedir + f'/{name}_циклы.png', width=Cm(22)),
        'elastic_pic' : InlineImage(doc, savedir + f'/{name}_elastic.png', width=Cm(18))
    }
    
    if m != None:
        context['m'] = m
    if protocol != None:
        context['protocol'] = protocol
    try:
        if results['defl_10'] != None:
            context['defl_10'] = f"{results['defl_10']:.3f}"
        if results['defl_20'] != None:
            context['defl_20'] = f"{results['defl_20']:.3f}"
        if results['defl_40'] != None:
            context['defl_40'] = f"{results['defl_40']:.3f}"
    except KeyError:
        pass
        
    doc.render(context=context)
    if protocol != None:
        doc.save(f'{savedir}/ДС-003-{test_date[:4]}-П{protocol}.docx')
    else:
        doc.save(f'{savedir}/ДС-003-{test_date[:4]}-П_{name}.docx')
        
        
def residualStarain_DocGenerator(name,
                         a,
                         b,
                         h,
                         m,
                         test_date,
                         protocol,
                         h_residual,
                         savedir,
                         ):

    template = ABS_PATH / 'ResidualStrain_Template.docx'
    doc = DocxTemplate(template)
    context = {
        'name':name,
        'test_date': transform_date(test_date),
        'a' : a,
        'b' : b,
        'h' : h,
        'h1' : h_residual,
        'resStrain' : f"{(1 - h_residual/h) *100:.2f}"
    }
    
    if m != None:
        context['m'] = m
    if protocol != None:
        context['protocol'] = protocol
        
    doc.render(context=context)
    if protocol != None:
        doc.save(f'{savedir}/ДС-003-{test_date[:4]}-ОД{protocol}.docx')
    else:
        doc.save(f'{savedir}/ДС-003-{test_date[:4]}-ОД_{name}.docx')