# ! /usr/secuer_console/env python
import argparse
# import warnings
# from asyncio.log import logger
from pathlib import Path
# coding=gbk
import logging, os
import matplotlib.pyplot as plt

import pandas as pd
import scanpy as sc
import sys
from secuer.secuer import (secuer, Read)
from secuer.secuerconsensus import secuerconsensus

version = '1.0.12'
import yaml
import numpy as np


def get_yaml_load_all(yaml_file):
    # open yaml file
    with open(yaml_file, 'r', encoding="utf-8") as f:
        all_data = yaml.safe_load_all(f.read())
    params = {}
    for u in all_data:
        params.update(u)
    return params


class Logger:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        logg = logging.StreamHandler()
        logg.setFormatter(fmt)
        self.logger.addHandler(logg)

    def info(self, message):
        self.logger.info(message)

    def war(self, message):
        self.logger.warn(message)

    def error(self, message):
        self.logger.error(message)


text_exts = {
    'csv',
    'tsv',
    'tab',
    'data',
    'txt',  # these four are all equivalent
}
avail_exts = {
                 'anndata',
                 'xlsx',
                 'h5',
                 'h5ad',
                 'mtx',
                 'mtx.gz',
                 'soft.gz',
                 'loom',
             } | text_exts


def main():
    description = 'Secuer: ultrafast, scalable and accurate clustering of single-cell RNA-seq data.'
    parser = argparse.ArgumentParser(prog='Clustring', description=description, usage='%(prog)s [options]')

    # secuer
    subparsers1 = parser.add_subparsers()
    parser1 = subparsers1.add_parser('S', help='Clustering scRNA-seq data using secuer.')
    # parser.add_argument('-h','--help',help="Show this help message and exit.")
    parser1.add_argument('-i', '--inputfile', dest='inputfile',
                         help=f'Input a file with {avail_exts}.')
    parser1.add_argument('-o', '--outfile', dest='outfile', help='The name of output file.', default='output')
    parser1.add_argument('-d', '--distance', dest='distance',
                         help='The metric to measure the dissimilarity between cells and anchors. Choose one from [cosine],euclidean,L1,sqeuclidean].',
                         default='euclidean')
    parser1.add_argument('-p', '--anchors', dest='p', type=int,
                         help='Specify the number of anchors.', default=1000)
    parser1.add_argument('-s', dest='seed', type=int,
                         help='Set the seed for selceting representatives randomly.', default=1)

    parser1.add_argument('--knn', dest='knn', type=int,
                         help='Specify the number of nearest neighbors.',
                         default=7)
    parser1.add_argument('--eskm', dest='eskMethod',
                         help='Specify the method for estimating the number of clusters. Choose one from [subGraph,BiGraph]',
                         default='subGraph')
    parser1.add_argument('--reso', dest='eskResolution', type=float,
                         help='Specify the resolution when eskm is subGraph.',
                         default=0.8)
    parser1.add_argument('--gapth', dest='gapth', type=int,
                         help='Specify the gap-th largest value when eskm is BiGraph.', default=4)
    parser1.add_argument('--cm', dest='clusterMethod',
                         help='Specify the method of clustering in Secuer.', default='Kmeans')

    parser1.add_argument('--Gaussiankernel', dest='Gaussiankernel',
                         help='Specify the gaussian kernel to build bipartite graph in Secuer.',
                         default='localscaled')

    parser1.add_argument('--multiProcessState', dest='multiProcessState', action='store_true',
                         help=' Weather use the multiple process.',
                         default=False)
    parser1.add_argument('--num_multiProcesses', dest='num_multiProcesses', type=int,
                         help='The number of parallel processes..',
                         default=4)

    parser1.add_argument('--transpose', action='store_true', dest='istranspose',
                         help='Whether transpose the the input file. Use it when input file is features by observations.',
                         default=False, )
    parser1.add_argument('--yaml', dest='yamlpath',
                         help='The yaml file path.')
    parser1.add_argument('--plot', action='store_true', dest='plot', default=False,
                         help='Whether return the umap and pca scatter plot.')
    parser1.add_argument('--markergene', action='store_true', dest='markergene', default=False,
                         help='Find the rank genes for characterizing groups.')
    parser1.set_defaults(func='S')  # Declare the name so that you can find out which subcommand the user entered later

    # secuer consensus
    parser2 = subparsers1.add_parser('C', help='Clustering scRNA-seq data using secuer-consensus.')
    parser2.add_argument('-i', '--inputfile', dest='inputfile',
                         help=f'Input a file with {avail_exts}.')
    parser2.add_argument('-o', '--outfile', dest='outfile',
                         help='The name of output file.', default='outputConsens')
    parser2.add_argument('-p', '--anchors', dest='p', type=int,
                         help='Specify the the number of anchors.', default=1000)
    parser2.add_argument('--knn', dest='knn', type=int,
                         help='Specify the number of nearest neighbors.',
                         default=7)
    parser2.add_argument('-M', '--Times', dest='M', type=int,
                         help='The times of consensus.',
                         default=5)
    parser2.add_argument('--multiProcessState', dest='multiProcessState', action='store_true',
                         help=' Weather use the multiple process.',
                         default=False)
    parser2.add_argument('--num_multiProcesses', dest='num_multiProcesses', type=int,
                         help='The number of parallel processes..',
                         default=4)
    parser2.add_argument('--transpose', action='store_true', dest='istranspose', default=False,
                         help='Whether transpose the the input file.')
    parser2.add_argument('--yaml', dest='yamlpath',
                         help='The yaml file path.')
    parser2.add_argument('--plot', action='store_true', dest='plot', default=False,
                         help='Whether return the umap and pca scatter plot.')
    parser2.add_argument('--markergene', action='store_true', dest='markergene', default=False,
                         help='Find the rank genes for characterizing groups.')
    parser2.set_defaults(func='C')  # Declare the name so that you can find out which subcommand the user entered later

    args = parser.parse_args()
    try:
        args.func
    except:
        print('Secuer: ultrafast, scalable and accurate clustering of single-cell RNA-seq data.')
        print('version:', version)
        parser.print_help()
        sys.exit()

    if args.func == 'S':
        if not args.inputfile:
            parser.print_help()
            print('Inputfile is required')
            sys.exit(1)

        params = get_yaml_load_all(args.yamlpath)

        assert Path(args.inputfile).exists(), 'inputfile does not exist'
        assert isinstance(args.p, int), 'p should be int'
        assert isinstance(args.knn, int), 'knn should be int'
        logg = Logger()
        # yaml_path = os.path.join(,"test.yaml")

        ### creat output dir
        if os.path.isfile(args.outfile):
            print(f'Error: cannot create a dir because  %s is exist as a file.')
            sys.exit(1)
        elif os.path.isdir(args.outfile):
            print('Warning: output dir is exist, write output result in existing dir.')
        else:
            os.mkdir(args.outfile)

        print(f"Your input parameters are: \ninputfile:{args.inputfile},\
             \t\np: {args.p},\t\nknn:{args.knn},\ndistance: {args.distance},\
             \t\ncm: {args.clusterMethod}\
             \t\noutfile:{args.outfile},\t\nseed:{args.seed}.")
        logg.info('Reading data...')
        data = Read(args.inputfile, istranspose=args.istranspose)
        logg.war(f'Your data contains {data.shape[0]} observations and {data.shape[1]} features.')
        data.var_names_make_unique()

        logg.info('filtering genes...')
        sc.pp.filter_genes(data,
                           min_counts=params['gene']['min_counts'], min_cells=params['gene']['min_cells'],
                           max_counts=params['gene']['max_counts'], max_cells=params['gene']['max_cells'])

        logg.info('filtering cell...')
        sc.pp.filter_cells(
            data,
            min_counts=params['cell']['min_counts'],
            min_genes=params['cell']['min_genes'],
            max_counts=params['cell']['max_counts'],
            max_genes=params['cell']['max_genes'])

        logg.info('normalizing data...')
        sc.pp.normalize_total(data, target_sum=params['norm']['target_sum'])

        sc.pp.log1p(data)
        logg.info('selecting highly variable genes...')
        try:
            sc.pp.highly_variable_genes(data,
                                        min_mean=params['hvg']['min_mean'],
                                        max_mean=params['hvg']['max_mean'],
                                        min_disp=params['hvg']['min_disp'],
                                        flavor=params['hvg']['flavor'],
                                        n_top_genes=params['hvg']['n_top_genes'],
                                        span=params['hvg']['span'])
            data = data[:, data.var.highly_variable]
            sc.pp.scale(data, max_value=10)
        except:
            sc.pp.scale(data, max_value=10)

        logg.war(f'Your data contains {data.shape[0]} observations and {data.shape[1]} features after preprocessing.')

        logg.info('performing PCA...')
        sc.tl.pca(data, svd_solver=params['pca']['svd_solver'])
        # print(data.obsm['X_pca'])
        logg.info('Run secuer...')
        res = secuer(fea=data.obsm['X_pca'],
                     distance=args.distance,
                     p=args.p,
                     Knn=args.knn,
                     clusterMethod=args.clusterMethod,
                     mode='secuer',
                     eskMethod=args.eskMethod,
                     eskResolution=args.eskResolution,
                     gapth=args.gapth,
                     Gaussiankernel=args.Gaussiankernel,
                     multiProcessState=args.multiProcessState,
                     num_multiProcesses=args.num_multiProcesses
                     )
        logg.info(f'Finished: The secuer finds {np.unique(res).shape[0]} clusters.')
        # data.obs['secuer'] = res
        print(f'Note: save result to {args.outfile}/SecuerResult.txt')
        np.savetxt(f'{args.outfile}/SecuerResult.txt', res, fmt='%d', delimiter='\t')
        data.obs['Secuer'] = pd.Categorical(res)
        if args.plot:
            os.chdir(args.outfile)
            # rcParams['figure.figsize'] = 4, 4
            sc.pp.neighbors(data)
            sc.tl.umap(data)
            with plt.rc_context({'figure.figsize': (4, 4)}):
                sc.pl.umap(data, color=['Secuer'], save='Secuer.pdf', show=False)
                sc.pl.pca(data, color=['Secuer'], save='Secuer.pdf', show=False)
        data.write(f'{args.outfile}/SecuerResult.h5ad')
    # ------------------------------------- consensus --------------------------------------------
    if args.func == 'C':
        if not args.inputfile:
            parser.print_help()
            print('Inputfile is required')
            sys.exit(1)
        assert Path(args.inputfile).exists(), 'inputfile does not exist'
        assert isinstance(args.p, int), 'p should be int'
        assert isinstance(args.knn, int), 'knn should be int'
        assert isinstance(args.M, int), 'M should be int'

        ### creat output dir
        if os.path.isfile(args.outfile):
            print(f'Error: cannot create a dir because  %s is exist as a file.')
            sys.exit(1)
        elif os.path.isdir(args.outfile):
            print('Warning: output dir is exist, write output result in existing dir.')
        else:
            os.mkdir(args.outfile)

        print(f"Your input parameters are: inputfile:{args.inputfile},\
             \np: {args.p},\nknn:{args.knn},\nM: {args.M}\
             \noutfile:{args.outfile}.")

        # yaml_path = os.path.join('./', "test.yaml")
        params = get_yaml_load_all(args.yamlpath)
        logg = Logger()
        logg.info('Reading data...')
        data = Read(args.inputfile, istranspose=args.istranspose)
        logg.war(f'Your data contains {data.shape[0]} observations and {data.shape[1]} features.')
        logg.info('filtering genes...')
        data.var_names_make_unique()
        # filter gene
        sc.pp.filter_genes(data,
                           min_counts=params['gene']['min_counts'], min_cells=params['gene']['min_cells'],
                           max_counts=params['gene']['max_counts'], max_cells=params['gene']['max_cells'])
        logg.info('filtering cells...')
        # filter cell
        sc.pp.filter_cells(
            data,
            min_counts=params['cell']['min_counts'],
            min_genes=params['cell']['min_genes'],
            max_counts=params['cell']['max_counts'],
            max_genes=params['cell']['max_genes'])

        logg.info('normalizing data...')
        # normalize
        sc.pp.normalize_total(data, target_sum=params['norm']['target_sum'])
        # log
        sc.pp.log1p(data)
        logg.info('selecting highly variable genes...')
        # hvg
        sc.pp.highly_variable_genes(data,
                                    min_mean=params['hvg']['min_mean'],
                                    max_mean=params['hvg']['max_mean'],
                                    min_disp=params['hvg']['min_disp'],
                                    flavor=params['hvg']['flavor'],
                                    n_top_genes=params['hvg']['n_top_genes'],
                                    span=params['hvg']['span'])

        data = data[:, data.var.highly_variable]
        logg.war(f'Your data contains {data.shape[0]} observations and {data.shape[1]} features after preprocessing.')
        logg.info('performing PCA...')
        sc.pp.scale(data, max_value=10)
        sc.tl.pca(data, svd_solver=params['pca']['svd_solver'])

        logg.info('Run secuer consensus...')
        res = secuerconsensus(fea=data.obsm['X_pca'],
                                 run_secuer=True,
                                 p=args.p,
                                 Knn=args.knn,
                                 M=args.M,
                                 multiProcessState=args.multiProcessState,
                                 num_multiProcesses=args.num_multiProcesses
                                 )

        # print(res)
        # data.obs['secuer'] = res
        logg.info(f'Finished: The secuer finds {np.unique(res).shape[0]} clusters')
        print(f'Note: save result to {args.outfile}/SecuerConsenResult.txt')
        np.savetxt(f'{args.outfile}/SecuerConsenResult.txt', res, fmt='%d', delimiter='\t')
        data.obs['Secuer'] = pd.Categorical(res)
        if args.plot:
            os.chdir(args.outfile)
            # rcParams['figure.figsize'] = 4, 4
            sc.pp.neighbors(data)
            sc.tl.umap(data)
            with plt.rc_context({'figure.figsize': (4, 4)}):
                sc.pl.umap(data, color=['Secuer'], save='SecuerConsesus.pdf', show=False)
                sc.pl.pca(data, color=['Secuer'], save='SecuerConsesus.pdf', show=False)
        data.write(f'{args.outfile}/SecuerConsenResult.h5ad')


if __name__ == '__main__':
    main()